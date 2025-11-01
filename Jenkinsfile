pipeline {
    agent any

    environment {
        PROJECT_DIR = "metabuildlab"
        VENV_DIR = "venv"
        PYTHON = "${VENV_DIR}/bin/python3"
    }

    stages {

        stage('Checkout') {
            steps {
                git branch: 'main', url: 'https://github.com/pkakuru/metabuildlab.git'
            }
        }

        stage('Setup Virtual Environment') {
            steps {
                sh '''
                    if [ ! -d "$VENV_DIR" ]; then
                        python3 -m venv $VENV_DIR
                    fi
                    source $VENV_DIR/bin/activate
                    pip install --upgrade pip
                    pip install -r requirements.txt
                '''
            }
        }

        stage('Database Migrations') {
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
                    nohup $VENV_DIR/bin/python3 manage.py runserver 0.0.0.0:8000 &
                '''
            }
        }
    }

    post {
        success {
            echo "✅ Meta Build Lab deployed successfully!"
        }
        failure {
            echo "❌ Build failed. Check Jenkins logs for errors."
        }
    }
}
