pipeline {
    agent any

    environment {
        VENV_DIR = "venv"
        PYTHON = "/usr/bin/python3"
    }

    stages {
        stage('Checkout Code') {
            steps {
                git branch: 'main', url: 'https://github.com/pkakuru/metabuildlab.git'
            }
        }

        stage('Setup Virtual Environment') {
            steps {
                sh '''
                #!/bin/bash
                echo "Creating or reusing virtual environment..."
                if [ ! -d "$VENV_DIR" ]; then
                    $PYTHON -m venv $VENV_DIR
                fi
                $VENV_DIR/bin/python -m pip install --upgrade pip
                $VENV_DIR/bin/python -m pip install -r requirements.txt
                '''
            }
        }

        stage('Run Migrations') {
            steps {
                sh '''
                #!/bin/bash
                echo "Running Django migrations..."
                $VENV_DIR/bin/python manage.py makemigrations --noinput
                $VENV_DIR/bin/python manage.py migrate --noinput
                '''
            }
        }

        stage('Collect Static Files') {
            steps {
                sh '''
                #!/bin/bash
                echo "Collecting static files..."
                $VENV_DIR/bin/python manage.py collectstatic --noinput
                '''
            }
        }

        stage('Restart Django Server') {
            steps {
                sh '''
                #!/bin/bash
                echo "Restarting Django development server..."
                pkill -f "manage.py runserver" || true
                nohup $VENV_DIR/bin/python manage.py runserver 0.0.0.0:8000 > server.log 2>&1 &
                sleep 5
                echo "Server started on port 8000"
                '''
            }
        }
    }

    post {
        success {
            echo "✅ Meta Build Lab successfully deployed at http://192.168.1.181:8000"
        }
        failure {
            echo "❌ Build failed — check Console Output for details."
        }
    }
}
