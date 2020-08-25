#!/usr/bin/env python
import argparse
import os


class Templates:

    ALL = 'all'
    TEMPLATES = ['schema_user', 'schema_transfer', 'create_new_functions', 'modify_constraints', 'delete_old_functions',
                 'print_forms', ALL]

    schema_user_template = """
USE {CurrentVersion}
GO
CREATE SCHEMA {CurrentVersion}
GO
CREATE LOGIN {CurrentVersion} WITH PASSWORD='PCLender123', DEFAULT_DATABASE={CurrentVersion}, CHECK_EXPIRATION=OFF, CHECK_POLICY=OFF
GO
CREATE USER {CurrentVersion} FOR LOGIN {CurrentVersion}
ALTER USER {CurrentVersion} WITH DEFAULT_SCHEMA={CurrentVersion}
ALTER ROLE db_owner ADD MEMBER {CurrentVersion}
CREATE LOGIN {CurrentVersion}_ado WITH PASSWORD='PCLender123', DEFAULT_DATABASE={CurrentVersion}, CHECK_EXPIRATION=OFF, CHECK_POLICY=OFF
GO
CREATE USER {CurrentVersion}_ado FOR LOGIN {CurrentVersion}_ado
ALTER USER {CurrentVersion}_ado WITH DEFAULT_SCHEMA={CurrentVersion}
ALTER ROLE db_owner ADD MEMBER {CurrentVersion}
ALTER ROLE [db_datareader] ADD MEMBER {CurrentVersion}_ado
"""

    schema_transfer_template = """
USE {CurrentVersion};
SELECT 'ALTER SCHEMA {CurrentVersion} TRANSFER ' + SCHEMA_NAME(schema_id) + '.' + name 
FROM sys.tables WHERE schema_id = SCHEMA_ID('Staging');
"""

    create_new_functions_template = """
USE [{CurrentVersion}]
GO
CREATE FUNCTION [{CurrentVersion}].[IU_CONTACT_DUPLICATE_LOGIN_NAME_CHECK](@LoginName varchar(40))
RETURNS INT
AS
BEGIN
  DECLARE  @ret_value INT

  SELECT @ret_value = COUNT(c.Login_Name)
    FROM {CurrentVersion}.Contact c
   WHERE c.Login_Name = @LoginName
     AND COALESCE(c.Contact_No_Longer_Employed, 'N') IN ('','N')
  RETURN @ret_value
END
GO
CREATE FUNCTION [{CurrentVersion}].[IU_EMPLOYEE_DUPLICATE_LOGIN_NAME_CHECK](@LoginName varchar(40))
RETURNS INT
AS
BEGIN
  DECLARE  @ret_value INT
  SELECT @ret_value = COUNT(e.Login_Name)
    FROM {CurrentVersion}.Employee e
   WHERE e.Login_Name = @LoginName
     AND COALESCE(e.No_Longer_Employed, 'N') IN ('','N')
  RETURN @ret_value
END
GO
"""

    modify_constraints_template = """
USE [{CurrentVersion}]
GO
ALTER TABLE [{CurrentVersion}].[Contact] DROP CONSTRAINT [UC_Contact_Login_Name]
GO
ALTER TABLE [{CurrentVersion}].[Contact]  WITH NOCHECK ADD  CONSTRAINT [UC_Contact_Login_Name] CHECK  (([{CurrentVersion}].[IU_CONTACT_DUPLICATE_LOGIN_NAME_CHECK]([Login_Name])<=(1)))
GO
ALTER TABLE [{CurrentVersion}].[Contact] CHECK CONSTRAINT [UC_Contact_Login_Name]
GO
ALTER TABLE [{CurrentVersion}].[Employee] DROP CONSTRAINT [UC_Employee_Login_Name]
GO
ALTER TABLE [{CurrentVersion}].[Employee]  WITH NOCHECK ADD  CONSTRAINT [UC_Employee_Login_Name] CHECK  (([{CurrentVersion}].[IU_EMPLOYEE_DUPLICATE_LOGIN_NAME_CHECK]([Login_Name])<=(1)))
GO
ALTER TABLE [{CurrentVersion}].[Employee] CHECK CONSTRAINT [UC_Employee_Login_Name]
GO
"""

    delete_old_functions_template = """
USE {CurrentVersion}
GO
DROP FUNCTION [adam].[IU_CONTACT_DUPLICATE_LOGIN_NAME_CHECK]
GO
DROP FUNCTION [adam].[IU_EMPLOYEE_DUPLICATE_LOGIN_NAME_CHECK]
GO
DROP SCHEMA adam
GO
USE {CurrentVersion}
GO
DROP USER adam
GO
DROP USER adam_ado
GO
"""

    print_forms_template = """
USE {CurrentVersion};
UPDATE {CurrentVersion}.[CfgInfo] SET [Item_Value] = 'MD ENV {CurrentVersion}' Where [Item_Name] = 'Database_Name';
UPDATE {CurrentVersion}.[CfgInfo] SET [Item_Value] = '\\pcldevdc01\env\{CurrentVersion}\Settings' Where [Item_Name] = 'Settings_Directory';
UPDATE {CurrentVersion}.[CfgInfo] SET [Item_Value] = '\\pcldevdc01\Imaging\env\{CurrentVersion}\Images' Where [Item_Name] = 'Images_Directory';
UPDATE {CurrentVersion}.[CfgInfo] SET [Item_Value] = '\\pcldevdc01\Imaging\env\{CurrentVersion}\thumbnails' Where [Item_Name] = 'ThumbnailDirectory';
UPDATE {CurrentVersion}.[CfgInfo] SET [Item_Value] = '172.19.200.24' Where [Item_Name] = 'HSHIndexIHServerIPAddress';
UPDATE {CurrentVersion}.[CfgInfo] SET [Item_Value] = '172.19.200.24' Where [Item_Name] = 'MortgageBotIHServerIP';
UPDATE {CurrentVersion}.[CfgInfo] SET [Item_Value] = '172.19.200.24' Where [Item_Name] = 'PasswordIHServerIP';
UPDATE {CurrentVersion}.[CfgInfo] SET [Item_Value] = '172.19.200.24' Where [Item_Name] = 'IndexRetrievalIHServerIPA';
UPDATE {CurrentVersion}.[loanid] SET [Loan_Number_Id] = 173000;
UPDATE {CurrentVersion}.[CfgInfo] SET [Item_Value] = 'smtp' Where [Item_Name] = 'SMTPMailHost';
UPDATE {CurrentVersion}.[CfgInfo] SET [Item_Value] = 'smtp' Where [Item_Name] = 'MailHost';
UPDATE {CurrentVersion}.[CfgInfo] SET [Item_Value] = '7:30:00 AM' Where [Item_Name] = 'IndexRetrievalTime';
UPDATE {CurrentVersion}.[CfgInfo] SET [Item_Value] = 'http://172.19.200.24:52036/soap/IICEWebServiceV1_0' Where [Item_Name] = 'IndexRetrievalURL';
UPDATE {CurrentVersion}.[CfgInfo] SET [Item_Value] = 'https://price.qa.pclender.com/MDENV{CurrentVersion}' Where [Item_Name] = 'PRICEBaseURL';
UPDATE {CurrentVersion}.[printdo] SET [Number_Of_Times_Used] = 0;
UPDATE {CurrentVersion}.[printdo] SET [Last_Used] = null;
"""

    @classmethod
    def build_file(cls, template_name, version_name, directory="."):
        filename = os.path.sep.join([directory, f"{template_name}_{args.version}.txt"])
        template_doc = getattr(cls, f"{template_name}_template")
        with open(filename, "w") as TEMPLATE_FILE:
            TEMPLATE_FILE.write(template_doc.format(CurrentVersion=version_name))
            print(f"Wrote: {filename}")


class CLIArgs:
    def __init__(self):
        self.parser = argparse.ArgumentParser()
        self.parser.add_argument("version", help="Version Name, spelled out: 10.2.3 = TenTwoThree")
        self.parser.add_argument(
            "-t", "--template", default=Templates.ALL, choices=Templates.TEMPLATES,
            help=f"Name of template to use; default = '{Templates.ALL}'")
        self.parser.add_argument("-d", "--dir", help="Location to store output files. Default = '.'", default='.')
        self.args = self.parser.parse_args()


if __name__ == '__main__':
    args = CLIArgs().args
    if args.template.lower() == Templates.ALL:
        for template_name in [t for t in Templates.TEMPLATES if not t == Templates.ALL]:
            Templates.build_file(template_name=template_name, version_name=args.version, directory=args.dir)
    else:
        Templates.build_file(template_name=args.template, version_name=args.version, directory=args.dir)
