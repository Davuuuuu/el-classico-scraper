def clean_up_docker = {
  sh script: "docker system prune -af --volumes >> /dev/null 2>&1 || true"  , label: "Docker system prune volumes"
  sh script: "docker system prune -af >> /dev/null 2>&1 || true " , label: "Docker system prune"
  sh script: "docker rm -f \$(docker ps -aq) >> /dev/null 2>&1 || true" , label: "Forceint to stop all containers"
}

pipeline {
    agent { label 'docker_comland' }
    
    stages {
        stage('Install') {
            steps {
                sh '''
                    curl -LsSf https://astral.sh/uv/install.sh | sh
                    export PATH="$HOME/.local/bin:$PATH"
                    uv venv .venv
                    . .venv/bin/activate
                    uv pip install -r requirements.txt
                '''
            }
        }
        stage('Launch scraper') {
            steps {
                withCredentials([
                    string(credentialsId: 'SLACK_WEBHOOK_URL', variable: 'SLACK_WEBHOOK_URL')
                ]) {
                    sh '''
                        . .venv/bin/activate
                        python el-classico-scraper.py "${SLACK_WEBHOOK_URL}"
                    '''
                }
            }
        }
        stage('Cleanup') {
          steps {
            script{
                clean_up_docker()
                }
          }
        }
    }
}