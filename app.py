from flask import Flask, render_template, request, redirect, url_for, flash
import os
import pandas as pd
import tempfile

import db_utils
import openai_utils

app = Flask(__name__)
app.secret_key = os.urandom(24)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        file = request.files['file']
        if file.filename.endswith('.csv'):
            question = request.form['question']
            with tempfile.NamedTemporaryFile(delete=False) as temp_csv:
                file.save(temp_csv.name)
                df = pd.read_csv(temp_csv.name)

            database = db_utils.dataframe_to_database(df, "Sales")
            fixed_sql_prompt = openai_utils.create_table_definition_prompt(df, "Sales")
            final_prompt = openai_utils.combine_prompts(fixed_sql_prompt, question)
            response = openai_utils.send_to_openai(final_prompt)
            proposed_query_postprocessed = db_utils.handle_response(response)
            result = db_utils.execute_query(database, proposed_query_postprocessed)

            flash(f"SQL Query: {proposed_query_postprocessed}")
            flash(f"Results: {result}")
            return redirect(url_for('index'))
        else:
            flash("Invalid file type. Please upload a CSV file.")
            return redirect(url_for('index'))
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
