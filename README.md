# Books for Rent

A Django-based service for managing book rentals. This project handles user registration, authentication, book inventory management, borrowings, and payments via Stripe. It also integrates with a Telegram bot to send notifications.

---

## Table of Contents

- [Overview](#overview)
- [API Reference](#api-reference)
  - [Books Service](#books-service)
  - [Users Service](#users-service)
  - [Borrowings Service](#borrowings-service)
  - [Payments Service](#payments-service)
- [Installation](#installation)
- [Configuration](#configuration)
  - [Environment Variables](#environment-variables)
  - [Stripe Setup](#stripe-setup)
  - [Telegram Bot Setup](#telegram-bot-setup)
- [Running the Project](#running-the-project)
- [Creating a Superuser](#creating-a-superuser)
- [License](#license)
- [Contact](#contact)

---

## Overview

Books for Rent is a learning project that demonstrates how to build a full-stack application using Django and Docker. The project includes:

- **Books Service:** CRUD operations for managing the inventory of books.
- **Users Service:** Handles user registration and JWT-based authentication.
- **Borrowings Service:** Allows users to borrow books, track active borrowings, and return books.
- **Payments Service:** Integrates Stripe for handling payments, including fines for overdue returns.
- **Telegram Bot:** Sends notifications about borrowings, returns, and overdue books.

---

## API Reference

### Books Service

Managing the quantity of books (CRUD for Books)

| Method    | URL               | Description                                   |
|-----------|-------------------|-----------------------------------------------|
| **POST**  | `/books/`         | Add a new book                                |
| **GET**   | `/books/`         | Retrieve a list of books                      |
| **GET**   | `/books/<id>/`    | Retrieve detailed information for a book      |
| **PUT/PATCH** | `/books/<id>/` | Update a book (including inventory management)|
| **DELETE**| `/books/<id>/`    | Delete a book                                 |

---

### Users Service

Managing authentication and user registration

| Method         | URL                        | Description                        |
|----------------|----------------------------|------------------------------------|
| **POST**       | `/users/`                  | Register a new user                |
| **POST**       | `/users/token/`            | Obtain JWT tokens                  |
| **POST**       | `/users/token/refresh/`    | Refresh JWT token                  |
| **GET**        | `/users/me/`               | Retrieve current user profile      |
| **PUT/PATCH**  | `/users/me/`               | Update user profile                |

---

### Borrowings Service

Managing users' borrowings of books

| Method         | URL                                                       | Description                                                                      |
|----------------|-----------------------------------------------------------|----------------------------------------------------------------------------------|
| **POST**       | `/borrowings/`                                            | Create a new borrowing record                                                    |
| **GET**        | `/borrowings/?user_id=...&is_active=...`                   | Retrieve borrowings by user ID and status (active/inactive)                       |
| **GET**        | `/borrowings/<id>/`                                       | Retrieve details of a specific borrowing                                         |
| **POST**       | `/borrowings/<id>/return/`                                | Set the actual return date (if overdue, triggers Stripe payment for fines)         |

---

### Payments Service

Managing payment operations via Stripe

| Method         | URL                      | Description                                           |
|----------------|--------------------------|-------------------------------------------------------|
| **GET**        | `/success/`              | Check successful Stripe payment                       |
| **GET**        | `/cancel/`               | Return payment canceled message                       |
| **GET**        | `/payments/`             | Retrieve a list of payments                           |
| **GET**        | `/payments/<id>/`        | Retrieve details of a specific payment                |

---

## Installation

1. **Clone the repository:**

   ```bash
   git clone https://github.com/Roman-Sokolov-V/books-for-rent.git
   cd books-for-rent
   ```
    Configure Environment Variables:

    Rename the sample environment file to .env:
   ```bash
    mv samle.env .env
   ```


Then, fill in all the required variables in the .env file. Example:

    # Django
    SECRET_KEY=your-django-secret-key
    DEBUG=True

    # Telegram Bot
    TELEGRAM_BOT_TOKEN=your-telegram-bot-token

    # Stripe
    STRIPE_PUBLISH_KEY=your-stripe-publishable-key
    STRIPE_SECRET_KEY=your-stripe-secret-key
    STRIPE_WEBHOOK_SECRET=your-stripe-webhook-secret
    STRIPE_DEVICE_NAME=your-device-name

    # PostgreSQL
    POSTGRES_DB=postgres
    POSTGRES_USER=postgres
    POSTGRES_PASSWORD=mypassword
    POSTGRES_HOST=db
    POSTGRES_PORT=5432
    PGDATA=/var/lib/postgresql/data

    Install Docker:

    Download and install https://www.docker.com/products/docker-desktop/ if you haven't already.

### Configuration
#### Environment Variables

Make sure all required environment variables are set in your .env file. This includes keys for Django, PostgreSQL, Stripe, and Telegram.
#### Stripe Setup

Sign up at [Stripe Dashboard](https://dashboard.stripe.com)
Get your Publishable Key and Secret Key. Add them to your .env as STRIPE_PUBLISH_KEY and STRIPE_SECRET_KEY.
Create a webhook endpoint (e.g., http://0.0.0.0:8000/payments/webhook/) in the Stripe Dashboard. Copy the webhook signing secret and add it to STRIPE_WEBHOOK_SECRET in your .env.

#### Telegram Bot Setup

Create a new bot using [BotFather](https://telegram.me/BotFather) and obtain the bot token.
Add the token to your .env as TELEGRAM_BOT_TOKEN.

1. Running the Project

    Start the Docker containers:
   ```bash
    docker-compose up --build
   ```
2. Wait for all services to initialize.

3. Create a superuser:
   ```bash
   docker-compose exec web python manage.py createsuperuser
   ```
Open a new terminal and run:

   ```bash
   docker-compose exec web python manage.py createsuperuser
   ```

4. Access the admin panel:

    Open http://0.0.0.0:8000/admin/ in your browser and log in with your superuser credentials.

5. Populate the database:  
        Create some book records via the admin panel or by using the API (e.g., obtaining a JWT token via /users/token/ and then sending POST requests to /books/).

6. Borrow a Book:  

    Use the endpoint /borrowings/ (with the POST method) to select a book and specify the expected return date. After borrowing, you will be redirected to a Stripe payment page if necessary.

7.  Check Payments:

    Access http://0.0.0.0:8000/payments/ to view your payments list.

8.  Return a Book:

    To return a book, use the endpoint /borrowings/<id>/return/ (replace <id> with your borrowing record ID). If the return is overdue, you will be directed to the Stripe payment page to pay for the overdue days with an additional fine.

9.  Telegram Notifications:  
*  Open your Telegram bot and send /start. 
*  Follow the prompts to enter your email and password (matching a user from your system). 
*  Once authenticated, you will receive notifications about new borrowings, returns, and daily reminders for overdue rentals.

### Creating a Superuser

To create a Django superuser:

1. Run the following command in your Docker container:
   ```bash
    docker-compose exec web python manage.py createsuperuser
   ```
2. Follow the prompts to enter a username, email, and password.

3.    After creation, you can log in to the admin panel at http://0.0.0.0:8000/admin/.

License

This project is licensed under the MIT License. See the LICENSE file for more details.
Contact

If you have any questions or issues, please open an issue in the GitHub repository or contact me at your-email@example.com.

Happy coding!


This README provides a clear structure, detailed instructions, and all the necessary information for users to set up, configure, and run your project. Feel free to adjust sections and add more details as your project evolves.
