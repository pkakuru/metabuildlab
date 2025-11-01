pipeline {
    agent any
    stages {
        stage('Verify Python Environment') {
            steps {
                sh '''
                echo "PATH: $PATH"
                which python3
                python3 --version
                which pip3
                pip3 --version
                '''
            }
        }
    }
}
