import sys
import json
import uuid
import os

sys.path.insert(0, os.path.abspath('backend'))

from app.database.seed import seed_database
import inspect

src = inspect.getsource(seed_database)

start_idx = src.find('courses = [')
end_idx = src.find('for course_data in courses:')
courses_code = src[start_idx:end_idx].strip()

courses_code = courses_code.replace('DifficultyLevel.BEGINNER', "'beginner'")
courses_code = courses_code.replace('DifficultyLevel.INTERMEDIATE', "'intermediate'")
courses_code = courses_code.replace('DifficultyLevel.ADVANCED', "'advanced'")

exec_scope = {}
exec(courses_code, exec_scope)
courses = exec_scope['courses']

sql_lines = [
    "-- =============================================================================",
    "-- SmartReco — Supabase 105+ Course Catalog Seeding Script",
    "-- Copy & Run this file in Supabase SQL Editor:",
    "-- https://supabase.com/dashboard/project/lrjxlsvgsfakpxwkibpk/sql",
    "-- =============================================================================",
    "",
    "INSERT INTO products (id, title, description, category, price, difficulty_level, duration_hours, tags, embedding_status) VALUES"
]

values = []
for idx, c in enumerate(courses):
    cid = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"smartreco-course-{idx+1}"))
    title = c['title'].replace("'", "''")
    desc = c['description'].replace("'", "''")
    cat = c['category'].replace("'", "''")
    diff = c['difficulty_level']
    price = c['price']
    duration = c['duration_hours']
    tags_json = json.dumps(c['tags']).replace("'", "''")
    values.append(f"('{cid}', '{title}', '{desc}', '{cat}', {price}, '{diff}', {duration}, '{tags_json}'::jsonb, 'indexed')")

sql_lines.append(",\n".join(values) + "\nON CONFLICT (id) DO UPDATE SET title = EXCLUDED.title, description = EXCLUDED.description;\n")

out_path = os.path.abspath('docs/supabase_seed_courses.sql')
with open(out_path, 'w', encoding='utf-8') as f:
    f.write("\n".join(sql_lines))

print(f"Successfully generated SQL for {len(courses)} courses at {out_path}!")
