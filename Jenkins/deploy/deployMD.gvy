pipeline {
    agent any
    
    environment {
        automation_dir = "/home/rhunt/BuildAutomation"
    }
    
    stages {
        stage('Define the Deployment Environment') {
            steps {
                script {
                    build_text = version_to_text("${env.BUILD_VERSION}")
                    los_repository = "${env.SVN}/LOS/branches/Maintenance/${env.BUILD_VERSION}"
                    if ("${env.PortNumber}" == "0") {
		                port_number = version_to_port("${env.BUILD_VERSION}")
                    } else {
                        port_number = "${env.PORT}"
                    }
                    if ("${env.ENV_NAME}" == "custom") {
                        env_name = env.CUSTOM_ENV
                        if (env_name == '') {
                            echo "ERROR: No custom name was provided, but a custom env was selected."
                            sh "exit 1"
                        }
                        std_env_port = version_to_port("${env.BUILD_VERSION}")
                    } else {
                        env_name = env.ENV_NAME
                    }
                    env_url = "application.${env_name}.pclender.com"
                }
        		echo "Installing/upgrading the '${env_name}' environment using ${env.BUILD_VERSION}:${port_number} (${build_text})"
        		echo "ENV URL: ${env_url}"
                echo "SVN Repo: ${los_repository}"
                echo "Use existing build: ${env.USE_EXISTING_BUILD}"
            }
        }
        
        stage('Get or Build Requested Image') {
            steps {        
                script {
                    if (env.USE_EXISTING_BUILD.toBoolean()) {
                        echo "USING EXISTING BUILD."
                    } else {
                        echo "KICKING OFF NEW BUILD."
                    }
                }
                echo "Set Build Triggers"
                echo "Futz with ServiceDeployer"
                echo "Update Patch Manager"
                echo "Set Jira Integration parameters"
            }
        }
        stage('Define Build Parameters') {
            steps {
                echo "Define Build Parameters (${build_text})"
            }
        }
        stage('Define the MS Win Service for MD instance') {
            steps {
                echo "Registering and Tweaking the Service"
            }
        }
        stage('Setup Database') {
            steps {
                echo "Restore DB from known snapshot"
                echo "Create and execute script to create Schema and user"
                echo "Create and execute script to create Schema Xfer"
                echo "Create and execute script to create new functions"
                echo "Execute script to modify constraints"
                echo "Delete oldd functions, schemas, and users"
                echo "Setup PrintForms info"
            }
        }
        stage('Automate Patch Manager') {
            steps {
                echo "Create script to run PatchManager"
            }
        }
    }
}

def version_to_text(b_ver) {
    return sh (script: "python3 ${env.automation_dir}/build_to_text.py ${b_ver}", returnStdout: true).trim()
}

def version_to_port(b_ver) {
    return sh (script: "python3 ${env.automation_dir}/build_to_port.py ${b_ver}", returnStdout: true).trim()
}