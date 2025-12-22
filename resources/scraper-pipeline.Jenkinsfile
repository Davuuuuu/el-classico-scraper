def clean_up_docker = {
  sh script: "docker system prune -af --volumes >> /dev/null 2>&1 || true"  , label: "Docker system prune volumes"
  sh script: "docker system prune -af >> /dev/null 2>&1 || true " , label: "Docker system prune"
  sh script: "docker rm -f \$(docker ps -aq) >> /dev/null 2>&1 || true" , label: "Forceint to stop all containers"
}

pipeline {
    agent { label 'docker_comland' }
    
    stages {
        stage('Launch scraper') {
            steps {
                withCredentials([
                    string(credentialsId: 'SLACK_WEBHOOK_URL', variable: 'SLACK_WEBHOOK_URL')
                ]) {
                    sh '''
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