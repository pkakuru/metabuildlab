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
                echo "Cleaning previous virtual environment if exists..."
                rm -rf venv

                echo "Creating a new virtual environment..."
                python3 -m venv venv

                echo "Removing any preinstalled pip..."
                rm -rf venv/lib/python3.12/site-packages/pip*

                echo "Installing stable pip 23.3.2..."
                venv/bin/python -m ensurepip --upgrade
                venv/bin/python -m pip install --force-reinstall pip==23.3.2

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

                echo "Starting Django server in background..."
                nohup $WORKSPACE/venv/bin/python manage.py runserver 0.0.0.0:8000 > django.log 2>&1 &

                sleep 5
                echo "✅ Django server started successfully on http://192.168.1.181:8000"
                '''
            }
        }

        stage('Verify Server') {
            steps {
                sh '''
                echo "Checking if Django server is running..."
                ps aux | grep runserver | grep -v grep || (echo "❌ Server not running!" && exit 1)
                '''
            }
        }

    }

    post {
        success {
            echo "✅ MetaBuildLab successfully deployed at http://192.168.1.181:8000"
        }
        failure {
            echo "❌ Build failed — check console output for errors."
        }
    }
}
