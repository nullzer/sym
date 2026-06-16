sym
===

Symfony 2.2 based application.

## Setup after cloning

Clone the repository, enter the project directory, and run the setup script:

```bash
git clone <repository-url> sym
cd sym
./setup.sh
```

The script checks for PHP and Composer, installs Composer dependencies, prepares
Symfony cache/log directories, runs the Symfony requirements check, clears the
development cache, and installs web assets.

If Composer is not installed globally, place `composer.phar` in the project root
and run the script again.

After setup, review `app/config/parameters.yml` for local database and mailer
settings. Serve the `web/` directory as the document root and open:

```text
/app_dev.php/demo/hello/Fabien
```
