import os
import sys

def main():
    if len(sys.argv) != 3:
        print("Usage: python create_migration.py <app_label> <migration_name>")
        sys.exit(1)

    app_label = sys.argv[1]
    migration_name = sys.argv[2]

    command = f"python manage.py makemigrations {app_label} --name {migration_name}"
    print(f"Executing: {command}")
    os.system(command)

if __name__ == "__main__":
    main()
