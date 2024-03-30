
# ERPNext Expense Management Module
This package contains an Expense Management Module for ERPNext.

## Required Data
All the required data like Workflows, and all the associated information comes with this package. No need to stress about that. You can however change it to suit your specific requirements.

## How to Install
On your instance terminal, run the below command to grab the code from GitHub to your instance: <pre><code> bench get-app https://github.com/Upeosoft-Limited/erpnext-expense-management-module.git </code></pre>

Once the command has completed the execution, you will need to install the app in every site where you want toe app to run. You can install this app with the below command: <pre><code> bench --site [SITE_NAME] install-app erpnext_expenses </code></pre>

When this command completes, the application is installed in your site. You will however need to run the migrate command, which ensures that all changes to the database have been effected to your site's database. If your site is in development mode, ensure that bench is running. If you are on production, supervisor will take care of this. The command to effect the migrations is as below: <pre><code> bench --site [SITE_NAME] migrate </code></pre>

At this point, your app is fully installed and database changes migrated. All you need to do is restart your instance. The commands to do that are below:

#### Development Environment 
<pre><code> bench start </code></pre>

If you receive a warning that bench is already running, run the below command:
<pre><code> bench restart </code></pre>

#### Production Environment
<pre><code> sudo supervisorctl restart all </code></pre>
