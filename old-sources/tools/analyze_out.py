import os
import re
from datetime import datetime

def extract_suspicious_data(text):
    return {
        "paths": re.findall(r'(/[a-zA-Z0-9_\-/.]+)', text),
        "windows_paths": re.findall(r'([A-Z]:\\[a-zA-Z0-9_\-\\/.]+)', text),
        "users": re.findall(r'\b(user|admin|root|guest|test)\b', text, re.IGNORECASE),
        "keywords": re.findall(r'\b(password|passwd|secret|conf|login)\b', text, re.IGNORECASE),
        "ip_like": re.findall(r'\b(?:\d{1,3}\.){3}\d{1,3}\b', text)
    }

def analyze_out_files(directory="results"):
    report = {}
    for file in os.listdir(directory):
        if file.endswith(".out"):
            with open(os.path.join(directory, file), 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                report[file] = extract_suspicious_data(content)
    return report

def save_markdown(report, outpath="results/analysis_report.md"):
    with open(outpath, 'w', encoding='utf-8') as f:
        f.write(f"# PrinterReaper - Analysis Report\n\n")
        f.write(f"_Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}_\n\n")
        for filename, data in report.items():
            f.write(f"## {filename}\n")
            for key, values in data.items():
                f.write(f"### {key}\n")
                if values:
                    for item in sorted(set(values)):
                        f.write(f"- {item}\n")
                else:
                    f.write("- None found\n")
                f.write("\n")

if __name__ == "__main__":
    result = analyze_out_files()
    save_markdown(result)
    print("[✓] Analysis complete. Report saved to results/analysis_report.md")
