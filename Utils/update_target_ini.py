import argparse
import configparser
import logging
import os
import re
import typing


class IniFile:
    def __init__(self, filespec: str) -> None:
        """
        Basic Ini File Constructor

        :param filespec: Filespec (path and name) of INI file to read.

        """
        self.file = filespec
        self.log = logging.getLogger(self.__class__.__name__)
        self.config = self.read_file()
        self.log.debug(f"IniFile '{self.__class__.__name__}' has been instantiated.")

    def read_file(self) -> configparser.ConfigParser:
        """
        Read and parse the Ini File.

        :return: configParser with file contents (or empty if file did not exist/was not found)

        """
        config = configparser.ConfigParser()
        if os.path.exists(self.file):
            config.read(self.file)
            self.log.debug(f"Parsed {self.file} successfully.")
        else:
            self.log.error(f"Specified log file ('{self.file}') was not found.")
        return config


class TargetIniFile(IniFile):

    CORE = 'Core'
    TARGETS = 'TARGETS'
    TEMPLATE_SECTION = 'dev_trunk'

    def verify_targets_are_defined(self) -> bool:
        """
        Perform a quick sanity check on the file to verify all relevant sections are defined and registered.

        :return: (bool) - True: all checks passed, False: discrepancies found.

        """
        self.log.debug(f'Verifying that target ini file has {self.CORE} section.')
        if self.CORE not in self.config.sections():
            self.log.error(f"'{self.CORE}' was not found as a section with the ini file.")
            return False

        self.log.debug(f'Verifying that target ini file {self.CORE} section has {self.TARGETS} option.')
        if not self.config.has_option(self.CORE, self.TARGETS):
            self.log.error(f"'{self.TARGETS}' was not found as an option with the '{self.CORE}' section.")
            return False

        # Get list of all registered sections in CORE:TARGETS, and a list of sections in the INI file.
        core_targets = set(self.config.get(self.CORE, self.TARGETS).split(','))
        targets_sections = set(self._get_target_sections())
        sections_match = core_targets == targets_sections
        self.log.debug(f"[{self.CORE}][{self.TARGETS}] and defined sections match 1:1? {sections_match}")

        # Record any mismatches
        if not sections_match:
            undefined_sections = core_targets - targets_sections
            unregistered_sections = targets_sections - core_targets
            if undefined_sections:
                self.log.error(f"The following sections are registered in {self.CORE} but are not defined "
                               f"as sections: {', '.join(undefined_sections)}")
            if unregistered_sections:
                self.log.error(f"The following sections are defined but are not registered in {self.CORE}: "
                               f"{', '.join(unregistered_sections)}")

        return sections_match

    def _get_target_sections(self) -> typing.List[str]:
        """
        Get all defined sections that are not the CORE section.

        :return: List of relevant sections.

        """
        return [section for section in self.config.sections() if section != self.CORE]

    def verify_all_sections_are_fully_defined(self) -> bool:
        """
        Compared all sections to a template section verify all options are correctly specified. If the
        missing section ends in a number, it is not considered missing, since some options can have multiple:
           price_folder <-- If this is missing, this is considered an error
           price_folder2 <--- If this is missing, that may be ok.

        :return: (bool) - True: All sections are correctly specified. False: Some sections are missing sections.

        """

        # Pattern to check if the name ends with a number: x > 1
        ends_with_number = re.compile(r'\w[2-9]+|\w\d{2,}$')

        overall_match = None
        expected_options = set(self.config.options(self.TEMPLATE_SECTION))
        self.log.debug(f'Check ini file sections are fully defined, using {self.TEMPLATE_SECTION} as the template.')
        for section in self._get_target_sections():
            options = set(self.config.options(section))
            all_options_match = options == expected_options

            if not all_options_match:
                template_has_more = [section for section in expected_options - options if
                                     ends_with_number.search(section) is None]
                target_has_more = [section for section in options - expected_options if
                                   ends_with_number.search(section) is None]

                if template_has_more:
                    self.log.error(f"Section '{section}' has missing options: {', '.join(template_has_more)}")
                if target_has_more:
                    self.log.error(f"Section '{section}' has unexpected options: {', '.join(target_has_more)}")

            overall_match = all_options_match if overall_match is None else overall_match and all_options_match

        self.log.info(f"All sections in the {self.file} file are fully defined: {overall_match}")
        return overall_match

    def write_file(self, filename: typing.Optional[str] = None) -> None:
        """
        Writes the file with the Core section first, and then in a custom order (TargetIniFile._sort_version)

        :param filename: (Optional) - Output file, if not specified, overwrite source file.

        :return: None

        """
        filename = filename or self.file

        # Determine proper section order
        reordered_sections = self._sort_version(self.config.sections())

        # Update config using sorted section order
        self.config._sections = dict([(section, self.config._sections[section]) for section in reordered_sections])

        # Sort each section's options alphabetically, and uppercase all option keywords
        # (ConfigParser does not maintain the case, so this restores it)
        for section in self.config._sections:
            self.config._sections[section] = dict([(name.upper(), value) for name, value in
                                                   sorted(self.config._sections[section].items(), key=lambda t: t[0])])

        # Update the CORE:TARGET string with the sections in the same order as stored in the file.
        new_target_str = ", ".join(self.config.sections()[1:])
        self.config.set(self.CORE, self.TARGETS, new_target_str)
        self.config.remove_option(self.CORE, self.TARGETS.lower())

        # Write the file
        with open(filename, "w") as INI:
            self.config.write(INI)
        self.log.info(f"Wrote output to {os.path.abspath(filename)}")

    def _sort_version(self, version_list: typing.List[str]) -> typing.List[str]:
        """
        Defined custom sort order used for writing the ini file.
        The first entry is CORE
        All subsequent elements are sorted by the following criteria:
           if the target has a <env>_<version> tag, sort by version
           else if the target has a <env>_<name> tag, sort by env
           else if the target has a <name> tag, sort by name

           This sorts by version (qe and dev are kept together per version), then sort all non-version tags.

        :param version_list: List of ini file sections

        :return: list of sorted ini file sections
        """
        order = {}
        reordered = [self.CORE]
        for version in version_list:

            # Skip this, it will be set as the first element.
            if version == self.CORE:
                continue

            parts = version.split('_')
            if len(parts) == 1:
                order[version.lower()] = version
            elif parts[1].isalpha():
                order[f"{parts[0].lower()}-{parts[1]}"] = version
            else:
                order[f"{parts[1]}-{parts[0].lower()}"] = version

        reordered.extend([version for key, version in sorted(order.items(), key=lambda v: v[0])])
        return reordered


if __name__ == '__main__':
    ini_file = "./targets.ini"
    updated_ini_file = "./targets.rewrite.ini"
    log_level = logging.DEBUG

    logging.basicConfig(filename='update_target_ini.log', level=log_level)

    target = TargetIniFile(ini_file)
    print(f"All targets defined: {target.verify_targets_are_defined()}")
    print(f"All targets are fully defined: {target.verify_all_sections_are_fully_defined()}")
    target.write_file(updated_ini_file)
