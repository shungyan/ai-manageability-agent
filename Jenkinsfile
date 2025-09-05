pipeline {
    agent any

    environment {
        DOCKER_IMAGE = "shungyan17/person_queue_count:latest"
        DOCKERHUB_CREDENTIALS = "dockerhub-credentials"
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Build Docker Image') {
            steps {
                script {
                    // Build only the custom service
                    sh 'docker build -t $DOCKER_IMAGE ./person_queue_count'
                }
            }
        }

        stage('Test with Docker Compose') {
            steps {
                script {
                    try {
                        // Build all services (will use local image for person_queue_count)
                        sh 'docker-compose -f docker-compose.yml build'

                        // Start services in detached mode
                        sh 'docker-compose -f docker-compose.yml up -d'

                        // Wait for services to settle
                        sh 'sleep 20'

                        // Example test: check logs for your service
                        sh 'docker logs person_queue_count | head -n 50'

                        // (Optional) You can add curl or pytest here to validate behavior
                    } finally {
                        // Always shut down compose
                        sh 'docker-compose -f docker-compose.yml down || true'
                    }
                }
            }
        }

        stage('Push to Docker Hub') {
            steps {
                script {
                    docker.withRegistry('https://index.docker.io/v1/', DOCKERHUB_CREDENTIALS) {
                        sh 'docker push $DOCKER_IMAGE'
                    }
                }
            }
        }
    }

    post {
        success {
            echo "✅ Successfully built, tested, and pushed $DOCKER_IMAGE"
        }
        failure {
            echo "❌ Build or test failed — image not pushed"
        }
    }
}
