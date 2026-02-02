# BASIS NASA Space Apps Challenge Bangladesh Hackathon Platform

A web-based competition management system built with Python and MySQL, designed to handle participant registrations, project submissions, judging processes, and administrative controls for science and arts competitions.

## Features

- **Multi-Role Authentication**: Support for participants, administrators, judges, and volunteers with role-based access control.
- **Participant Management**: Registration, team member management, and project information submission.
- **Submission System**: File upload system for project submissions with deadline management.
- **Judging System**: Comprehensive scoring system with multiple criteria (influence, creativity, validity, relevance, presentation).
- **Room Management**: Assign judges, volunteers, and projects to specific rooms for organized judging sessions.
- **Administrative Dashboard**: Full control over applications, user management, results processing, and data export.
- **Real-time Results**: Automated result calculation and export functionality.
- **Security**: Password hashing, session management, and secure file uploads.

## Prerequisites

- Python 3.8+
- MySQL 5.7+ (or MariaDB)
- pip (Python package manager)

## Installation

1. **Clone the repository:**

   ```bash
   git clone https://github.com/your-username/nsac-competition-system.git
   cd nsac-competition-system
   ```

2. **Create a virtual environment:**

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

4. **Set up the database:**
   - Install and start MySQL server
   - Create a database named `hackathon_db` (or update `DB_NAME` in `config.py`)
   - Update database credentials in `config.py` or set environment variables:
     ```bash
     export DB_HOST=127.0.0.1
     export DB_PORT=3306
     export DB_USER=root
     export DB_PASSWORD=your_password
     export DB_NAME=hackathon_db
     ```

5. **Configure application settings:**
   - Update `APP_SECRET` in `config.py` with a secure random string
   - Set `DEBUG=0` for production
   - Configure `BASE_URL` for your deployment

## Usage

1. **Run database migrations:**

   ```bash
   python wsgi_server.py
   ```

   This will create all necessary tables and insert a default admin user.

2. **Start the development server:**

   ```bash
   python wsgi_server.py
   ```

   The application will be available at `http://127.0.0.1:8000`

3. **Access the application:**
   - **Admin Login**: Use `admin@gmail.com` / `admin123` (change password after first login)
   - **Public Access**: Register new accounts or login with existing credentials

## Configuration

Key configuration options in `config.py`:

- **Database Settings**: `DB_CONFIG` - MySQL connection parameters
- **Security**: `APP_SECRET` - Secret key for sessions and security
- **Uploads**: `UPLOAD_DIR` - Directory for file submissions (max 20MB)
- **Sessions**: `SESSION_EXPIRE_DAYS` - Session lifetime
- **Deadlines**: Configurable registration, project info, and submission deadlines

## Database Schema

The system uses the following main tables:

- `users` - User accounts with roles
- `participant_applications` - Registration applications
- `projects` - Project information and team members
- `submissions` - File submissions
- `evaluations` - Judge scores and comments
- `room` - Judging rooms
- `room_user` - Room assignments for judges/volunteers
- `project_room` - Project assignments to rooms
- `make_scores` - Detailed scoring criteria

## API Endpoints

### Participant Routes

- `GET /` - Home page
- `GET/POST /login` - Participant login
- `GET/POST /register` - Participant registration

### Participant Routes

- `GET /participant/dashboard` - Participant dashboard
- `POST /participant/team-members` - Save team information
- `POST /participant/project` - Save project details

### Admin,Judge And Volunteer Routes

- `GET/POST /portal-login` - Admin,Judge And Volunteer login
- `GET/POST /portal-register` - Judge And Volunteer registration

### Admin Routes

- `GET /admin/dashboard` - Admin dashboard
- `GET /admin/applications` - Manage applications
- `GET /admin/rooms` - Room management
- `GET /admin/judges-volunteers` - Manage judges and volunteers
- `GET /admin/results` - View and process results

### Judge Routes

- `GET /judge/dashboard` - Judge dashboard
- `GET/POST /judge/score` - Score projects

### Volunteer Routes

- `GET /volunteer/dashboard` - Volunteer dashboard
- `GET /volunteer/view` - View assigned tasks

## Development

### Project Structure

```
├── app.py                 # Main WSGI application
├── config.py              # Configuration settings
├── routes.py              # URL routing
├── wsgi_server.py        # Development server
├── requirements.txt       # Python dependencies
├── auth/                  # Authentication modules
├── controllers/           # Route handlers
├── db/                    # Database models and migrations
├── static/                # Static assets (CSS, JS)
├── templates/             # HTML templates
├── uploads/               # File upload directory
└── utils/                 # Utility functions
```


### Code Style

- Follow PEP 8 Python style guidelines
- Use meaningful variable and function names
- Add docstrings to functions and classes

## Deployment

1. **Production Server Setup:**
   - Use a WSGI server like Gunicorn or uWSGI
   - Configure a reverse proxy (nginx/Apache)
   - Set environment variables for production
   - Disable debug mode

2. **Environment Variables:**

   ```bash
   export DEBUG=0
   export APP_SECRET=your-production-secret
   export DB_HOST=your-db-host
   export DB_PASSWORD=your-secure-password
   export BASE_URL=https://your-domain.com
   ```

3. **Database Backup:**
   - Regularly backup the MySQL database
   - Store backups securely

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Guidelines

- Write clear, concise commit messages
- Add tests for new features
- Update documentation as needed
- Follow the existing code style

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

For support, please open an issue on GitHub or contact the maintainers.

## Acknowledgments

- Built with Python and MySQL
- Uses Werkzeug for WSGI serving
- PyMySQL for database connectivity
