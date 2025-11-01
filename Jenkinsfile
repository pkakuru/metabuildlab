pipeline {
    agent any

    environment {
        VENV_DIR = "venv"
        PYTHON = "/usr/bin/python3"
    }

    stages {
        stage('Checkout') {
            steps {
                git branch: 'main', url: 'https://github.com/pkakuru/metabuildlab.git'
            }
        }

        stage('Setup Python Environment') {
            steps {
                sh '''
                if [ ! -d "$VENV_DIR" ]; then
                    $PYTHON -m venv $VENV_DIR
                fi
                source $VENV_DIR/bin/activate
                pip install --upgrade pip
                pip install -r requirements.txt || true
                '''
            }
        }

        stage('Migrate Database') {
            steps {
                sh '''
                source $VENV_DIR/bin/activate
                python manage.py makemigrations
                python manage.py migrate
                '''
            }
        }

        stage('Collect Static Files') {
            steps {
                sh '''
                source $VENV_DIR/bin/activate
                python manage.py collectstatic --noinput
                '''
            }
        }

        stage('Run Django Server') {
            steps {
                sh '''
                pkill -f "manage.py runserver" || true
                nohup $VENV_DIR/bin/python manage.py runserver 0.0.0.0:8000 &
                '''
            }
        }
    }

    post {
        success {
            echo "✅ Meta Build Lab deployed successfully!"
        }
        failure {
            echo "❌ Build failed — check logs for details."
        }
    }
}
