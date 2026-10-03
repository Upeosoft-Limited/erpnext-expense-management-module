
# ERPNext Expense Management Module
This package contains an Expense Management Module for ERPNext.

## Expense Report Workflow
The app includes a simple default workflow for `Expense Report` as a starting template. It is designed for a single cashier or operator. Companies can extend it with manager approval, finance review, rejection, or amendment states.

Workflow records are site data. If a company customizes the workflow in a production site, do not export that customized record back into this app's fixtures unless it is intended to become the shared default for every site. Test fixture changes on a staging site before running production migrations.

The workflow must include a transition whose action is exactly `Create Journal Entries`. When that action is used, the app creates and submits the Journal Entry in the background using the report's `Paying Account` and expense accounts. The transition condition should require `doc.company` and `doc.paying_account`.

For a single-cashier company, a simple setup is:

1. Create `Draft` with `Allow Edit` set to `All`.
2. Create a final state such as `Journals Created` with document status `1`.
3. Add `Create Journal Entries` from `Draft` to the final state.
4. Enable `Allow Self Approval` and allow the cashier's role, such as `Accounts User`.
5. Mark intermediate review states as optional if you want to keep them available for future growth without forcing them into the current process.

The `Paying Account` field is required while the report is in Draft. You can add manager, finance, rejection, or amendment states later without changing the app code.

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
