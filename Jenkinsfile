pipeline {
    agent any

    stages {
        stage('Checkout Code') {
            steps {
                git branch: 'main', url: 'https://github.com/pkakuru/metabuildlab.git'
            }
        }

        stage('Setup Virtual Environment') {
            steps {
                sh '''
                echo "Creating or reusing virtual environment..."
                python3 -m venv venv
                echo "Upgrading pip to a stable version..."
                venv/bin/python -m pip install --upgrade "pip<24"
                echo "Installing project dependencies..."
                venv/bin/python -m pip install -r requirements.txt
                '''
            }
        }


        stage('Run Migrations') {
            steps {
                sh '''
                echo "Running Django migrations..."
                venv/bin/python manage.py makemigrations --noinput
                venv/bin/python manage.py migrate --noinput
                '''
            }
        }

        stage('Collect Static Files') {
            steps {
                sh '''
                echo "Collecting static files..."
                venv/bin/python manage.py collectstatic --noinput || true
                '''
            }
        }

        stage('Restart Django Server') {
            steps {
                sh '''
                echo "Restarting Django development server..."
                pkill -f "manage.py runserver" || true
                sleep 3
                nohup $WORKSPACE/venv/bin/python manage.py runserver 0.0.0.0:8000 > django.log 2>&1 &
                echo "✅ Django server started successfully on port 8000"
                '''
            }
        }
    }

    post {
        success {
            echo "MetaBuildLab successfully deployed at http://192.168.1.181:8000"
        }
        failure {
            echo "❌ Build failed — check console output for errors."
        }
    }
}
