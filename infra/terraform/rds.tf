# Managed AWS RDS PostgreSQL 16
resource "aws_db_subnet_group" "rds" {
  name       = "${var.app_name}-db-subnet-group"
  subnet_ids = aws_subnet.private[*].id

  tags = {
    Name = "${var.app_name}-db-subnets"
  }
}

resource "aws_security_group" "rds" {
  name        = "${var.app_name}-rds-sg"
  description = "Allow inbound PostgreSQL traffic strictly from ECS app containers"
  vpc_id      = aws_vpc.main.id

  ingress {
    description     = "PostgreSQL from ECS tasks"
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.ecs.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.app_name}-rds-sg"
  }
}

resource "aws_db_instance" "postgres" {
  identifier        = "${var.app_name}-postgres"
  engine            = "postgres"
  engine_version    = "16.1"
  instance_class    = "db.t4g.micro"
  allocated_storage = 20
  storage_type      = "gp3"
  storage_encrypted = true

  db_name  = var.db_name
  username = var.db_username
  password = var.db_password

  db_subnet_group_name   = aws_db_subnet_group.rds.name
  vpc_security_group_ids = [aws_security_group.rds.id]

  backup_retention_period = 7
  backup_window           = "03:00-04:00"
  maintenance_window      = "Sun:04:30-Sun:05:30"
  skip_final_snapshot     = true
  deletion_protection     = false

  tags = {
    Name = "${var.app_name}-postgres-db"
  }
}
