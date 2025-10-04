# 📤 Wiki Upload Instructions

How to upload the PrinterReaper wiki to GitHub.

---

## 📋 Prerequisites

1. GitHub repository with wiki enabled
2. Git installed on your system
3. GitHub account with push access

---

## 🚀 Quick Upload (Recommended)

### Step 1: Enable Wiki on GitHub

1. Go to your repository on GitHub
2. Click "Settings"
3. Scroll to "Features"
4. Check "Wikis"
5. Click "Save"

### Step 2: Clone Wiki Repository

```bash
# Clone the wiki repo (separate from main repo)
git clone https://github.com/yourusername/PrinterReaper.wiki.git

# Enter wiki directory
cd PrinterReaper.wiki
```

### Step 3: Copy Wiki Files

```bash
# Copy all wiki files from PrinterReaper/wiki/ to wiki repo
cp ../PrinterReaper/wiki/*.md .

# Verify files copied
ls -la
```

### Step 4: Commit and Push

```bash
# Add all files
git add .

# Commit
git commit -m "docs: Add complete wiki documentation for v2.3.4

Added comprehensive wiki documentation:
- 13 wiki pages
- ~6,000 lines of documentation
- Complete command reference
- Installation guides for all platforms
- Security testing workflows
- Attack vector documentation
- Real-world examples
- FAQ and troubleshooting

Coverage:
- All 54 commands documented
- All platforms covered (Linux, Windows, macOS, BSD)
- Security best practices
- Legal considerations
"

# Push to GitHub
git push origin master
```

---

## 📝 Manual Upload (Alternative)

If you prefer manual upload:

### Via GitHub Web Interface

1. Go to Wiki tab in your repository
2. Click "Create the first page"
3. Copy content from `wiki/Home.md`
4. Paste and save
5. Repeat for each page

**Order to create:**
1. Home
2. Installation
3. Quick-Start
4. Commands-Reference
5. PJL-Commands
6. Security-Testing
7. Examples
8. Attack-Vectors
9. Architecture
10. FAQ
11. Troubleshooting
12. Contributing
13. _Sidebar

---

## ✅ Verification

After upload, verify:

1. **Home page displays correctly**
   - Go to Wiki tab
   - Home page should load

2. **Sidebar works**
   - Check navigation on left
   - All links work

3. **Internal links work**
   - Click through wiki pages
   - Verify no broken links

4. **Formatting correct**
   - Code blocks render
   - Tables display properly
   - Lists formatted correctly

---

## 🔄 Updating Wiki

To update in the future:

```bash
# 1. Go to wiki repo
cd PrinterReaper.wiki

# 2. Pull latest
git pull origin master

# 3. Edit files
nano Home.md

# 4. Commit changes
git add Home.md
git commit -m "docs: Update home page"

# 5. Push
git push origin master
```

---

## 📚 Wiki Files Created

```
wiki/
├── Home.md                     # Wiki home (1,200 lines)
├── Installation.md             # Install guide (800 lines)
├── Quick-Start.md              # Quick start (600 lines)
├── Commands-Reference.md       # All commands (500 lines)
├── PJL-Commands.md             # PJL details (1,200 lines)
├── Security-Testing.md         # Security guide (600 lines)
├── Examples.md                 # Practical examples (700 lines)
├── Attack-Vectors.md           # Attack techniques (500 lines)
├── Architecture.md             # Technical architecture (600 lines)
├── FAQ.md                      # Questions (600 lines)
├── Troubleshooting.md          # Problem solving (500 lines)
├── Contributing.md             # Contribution guide (400 lines)
├── _Sidebar.md                 # Navigation menu (40 lines)
└── WIKI_README.md              # This file (200 lines)
```

**Total**: ~8,440 lines of documentation

---

## 🎯 Success Checklist

After upload, check:

- [ ] Home page loads at wiki URL
- [ ] Sidebar appears on all pages
- [ ] All internal links work
- [ ] Code blocks render correctly
- [ ] Tables display properly
- [ ] No 404 errors
- [ ] Search works

---

## 🚨 Common Issues

### Issue: "Repository not found"

**Solution:**
```bash
# Check remote URL
git remote -v

# Update if wrong
git remote set-url origin https://github.com/yourusername/PrinterReaper.wiki.git
```

### Issue: "Permission denied"

**Solution:**
```bash
# Set up SSH key or use HTTPS with token
git remote set-url origin https://YOUR_TOKEN@github.com/yourusername/PrinterReaper.wiki.git
```

### Issue: "Wiki not enabled"

**Solution:**
- Go to repo settings on GitHub
- Enable Wiki feature
- Try again

---

<div align="center">

**Wiki Upload Instructions**  
Complete guide to publishing the wiki on GitHub

</div>

