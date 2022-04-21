# db_to_excel

## Getting started

Takes Horos Database and naming convention and exports to excel file

1. git pull <https://github.com/ryanapfel/db_to_excel.git>
2. conda env create --file requirements.yml
3. Make sure config.cfg file contains all the correct paths to the database and study pages

Note: Be careful with relative paths. You might need to play around with paths until it works

### Email

[better instructions](https://www.thepythoncode.com/article/use-gmail-api-in-python)

1. follow instructions from above download json credentials and rename them to "credentials.json"
2. create folder in src folder called "secrets"
2. insert credentials into src/secrets
3. complete auth flow

## Usage

Export all from database to default master location

```
dblog all
```

Add unresolved sheet and all subjects grouped by their timepoints

```
dblog all -u -t
```

Select an alternate database and export to a non default location

```
dblog all --db_path=<database> --output_path=<spreadsheet directory> --output_file=<spreadsheet name>
```

Create spreadsheet for a specific study. Study will be exported to default study location if set with name studyname_tracker.xlsx

```
dblog study --study=studyname -u
```

File name will be exported with the current date and time as a suffix. EX: studyname_tracker_4_2_2023.xlsx

```
dblog study --study=studyname -u -dt
```
