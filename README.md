# 1. Create virtual environment
```
python -m venv .venv
```
Activate virtual enviroment
```
.\.venv\Scripts\Activate.ps1

```

Install needed packages for my project
```
python -m pip install --upgrade pip
python -m pip install langchain langchain-community langchain-openai faiss-cpu pypdf python-dotenv
```

Had to stop SSL
```
 PS C:\Users\mirei\OneDrive\Desktop\llm-pdf-project> Remove-Item Env:SSLKEYLOGFILE -ErrorAction SilentlyContinue
>> $env:SSLKEYLOGFILE = $null
```


Basic factual questions (should be EASY for your model)
What is the title of the project?
Which organization is leading the project?
What is the total funding requested?
What is the project duration?
Which region does the project target?