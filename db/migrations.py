#   """
#   NSAC Competition Management System - Database Migrations

#   This module handles database schema creation and initialization.
#   It defines all tables for the competition management system and creates a default admin user.
#   """

from db.database import execute

def migrate():
#   """
#   Execute database migrations to create all necessary tables.

#   Creates tables for users, sessions, site config, participant applications,
#   projects, submissions, evaluations, rooms, and scoring data.
#   Also inserts a default admin user.
#   """
    # users
    execute("""
    CREATE TABLE IF NOT EXISTS users (
      id BIGINT PRIMARY KEY AUTO_INCREMENT,
      name VARCHAR(120) NOT NULL,
      phone VARCHAR(120) NULL,
      designation VARCHAR(120) NULL,
      organization VARCHAR(120) NULL,
      email VARCHAR(190) NOT NULL UNIQUE,
      password_hash VARCHAR(255) NOT NULL,
      role ENUM('participant','admin','judge','volunteer') NOT NULL DEFAULT 'participant',
      status ENUM('active','inactive') NOT NULL DEFAULT 'active',
      created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """)

    # sessions
    execute("""
    CREATE TABLE IF NOT EXISTS sessions (
      id BIGINT PRIMARY KEY AUTO_INCREMENT,
      user_id BIGINT NOT NULL,
      session_token VARCHAR(128) NOT NULL UNIQUE,
      expires_at DATETIME NOT NULL,
      created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
      INDEX(user_id),
      CONSTRAINT fk_sessions_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """)

    # site config
    execute("""
    CREATE TABLE IF NOT EXISTS site_config (
      id BIGINT PRIMARY KEY AUTO_INCREMENT,
      `key` VARCHAR(120) NOT NULL UNIQUE,
      `value` TEXT NULL,
      updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """)

    # participant applications
    execute("""
    CREATE TABLE IF NOT EXISTS participant_applications (
      id BIGINT PRIMARY KEY AUTO_INCREMENT,
      user_id BIGINT NOT NULL,
      data_json JSON NULL,
      final_score DECIMAL(10,2) NULL,
      status ENUM('pending','approved','rejected') NOT NULL DEFAULT 'pending',
      created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
      updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
      INDEX(user_id),
      CONSTRAINT fk_app_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """)

    # projects
    execute("""
    CREATE TABLE IF NOT EXISTS projects (
      id BIGINT PRIMARY KEY AUTO_INCREMENT,
      participant_id BIGINT NOT NULL,
      title VARCHAR(255) NULL,
      description TEXT NULL,
      team_members_json JSON NULL,
      updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
      UNIQUE KEY uniq_participant (participant_id),
      CONSTRAINT fk_project_participant FOREIGN KEY (participant_id) REFERENCES users(id) ON DELETE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """)

    # submissions
    execute("""
    CREATE TABLE IF NOT EXISTS submissions (
      id BIGINT PRIMARY KEY AUTO_INCREMENT,
      project_id BIGINT NOT NULL,
      file_path VARCHAR(500) NOT NULL,
      status ENUM('submitted','reviewed') NOT NULL DEFAULT 'submitted',
      submitted_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
      INDEX(project_id),
      CONSTRAINT fk_sub_project FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """)

    # evaluations
    execute("""
    CREATE TABLE IF NOT EXISTS evaluations (
      id BIGINT PRIMARY KEY AUTO_INCREMENT,
      judge_id BIGINT NOT NULL,
      project_id BIGINT NOT NULL,
      score INT NOT NULL,
      comment TEXT NULL,
      created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
      UNIQUE KEY uniq_judge_project (judge_id, project_id),
      CONSTRAINT fk_ev_judge FOREIGN KEY (judge_id) REFERENCES users(id) ON DELETE CASCADE,
      CONSTRAINT fk_ev_project FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """)

    # -----------------------------
    # ✅ ROOM MODULE TABLES (NEW)
    # -----------------------------

    # room
    execute("""
    CREATE TABLE IF NOT EXISTS room (
      id BIGINT PRIMARY KEY AUTO_INCREMENT,
      name VARCHAR(191) NOT NULL,
      status ENUM('active','inactive') NOT NULL DEFAULT 'active',
      created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """)

    # room_user (assign judges & volunteers to room)
    execute("""
    CREATE TABLE IF NOT EXISTS room_user (
      id BIGINT PRIMARY KEY AUTO_INCREMENT,
      user_id BIGINT NOT NULL,
      room_id BIGINT NOT NULL,
      created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
      UNIQUE KEY uniq_room_user (user_id, room_id),
      INDEX idx_room_user_room (room_id),
      INDEX idx_room_user_user (user_id),
      CONSTRAINT fk_room_user_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
      CONSTRAINT fk_room_user_room FOREIGN KEY (room_id) REFERENCES room(id) ON DELETE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """)

    # project_room (assign projects to room)
    execute("""
    CREATE TABLE IF NOT EXISTS project_room (
      id BIGINT PRIMARY KEY AUTO_INCREMENT,
      projects_id BIGINT NOT NULL,
      room_id BIGINT NOT NULL,
      created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
      UNIQUE KEY uniq_project (projects_id),
      INDEX idx_project_room_room (room_id),
      INDEX idx_project_room_project (projects_id),
      CONSTRAINT fk_project_room_project FOREIGN KEY (projects_id) REFERENCES projects(id) ON DELETE CASCADE,
      CONSTRAINT fk_project_room_room FOREIGN KEY (room_id) REFERENCES room(id) ON DELETE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """)

    # make_scores
    execute("""
      CREATE TABLE IF NOT EXISTS make_scores (
        id BIGINT PRIMARY KEY AUTO_INCREMENT,
        user_id BIGINT NOT NULL,
        registration_id BIGINT NOT NULL,

        influence INT NOT NULL,
        creativity INT NOT NULL,
        validity INT NOT NULL,
        relevance INT NOT NULL,
        presentation INT NOT NULL,

        round_influence INT NOT NULL,
        round_creativity INT NOT NULL,
        round_validity INT NOT NULL,
        round_relevance INT NOT NULL,
        round_presentation INT NOT NULL,

        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

        UNIQUE KEY uniq_judge_reg (user_id, registration_id),
        INDEX idx_reg (registration_id),
        CONSTRAINT fk_make_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
        CONSTRAINT fk_make_reg FOREIGN KEY (registration_id) REFERENCES participant_applications(id) ON DELETE CASCADE
      ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """)
    # default admin (if not exists)
    from db.database import query_one, execute as exec2
    exists = query_one("SELECT id FROM users WHERE email=%s", ("admin@gmail.com",))
    if not exists:
        from auth.security import hash_password
        exec2(
            "INSERT INTO users (name,email,password_hash,role) VALUES (%s,%s,%s,%s)",
            ("Admin", "admin@gmail.com", hash_password("admin123"), "admin")
        )

if __name__ == "__main__":
    migrate()
    print("✅ Migration complete")
