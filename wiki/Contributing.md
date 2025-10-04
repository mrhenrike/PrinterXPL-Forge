# 🤝 Contributing to PrinterReaper

We welcome contributions! This guide explains how to contribute to PrinterReaper.

---

## 🎯 Ways to Contribute

### 1. Report Bugs 🐛
Found a bug? Help us fix it!
- Open an issue on GitHub
- Include reproduction steps
- Provide error messages
- Mention your environment

### 2. Suggest Features 💡
Have an idea? We'd love to hear it!
- Open a feature request
- Explain the use case
- Describe expected behavior
- Propose implementation (optional)

### 3. Improve Documentation 📚
Documentation is always welcome!
- Fix typos
- Add examples
- Clarify explanations
- Translate to other languages

### 4. Submit Code 💻
Want to code? Great!
- Fork the repository
- Create a feature branch
- Write clean code
- Submit a pull request

### 5. Test & Provide Feedback 🧪
Help us test!
- Test on different printers
- Test on different OS platforms
- Report compatibility issues
- Share success stories

---

## 🚀 Getting Started

### 1. Fork & Clone

```bash
# Fork on GitHub first
# Then clone your fork
git clone https://github.com/YOUR_USERNAME/PrinterReaper.git
cd PrinterReaper

# Add upstream remote
git remote add upstream https://github.com/ORIGINAL/PrinterReaper.git
```

### 2. Create Branch

```bash
# Create feature branch
git checkout -b feature/my-awesome-feature

# Or bugfix branch
git checkout -b fix/issue-123
```

### 3. Set Up Development Environment

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install development dependencies
pip install pylint black pytest
```

---

## 💻 Development Guidelines

### Code Style

**Follow PEP 8:**
```python
# Good
def my_function(arg1, arg2):
    """Function docstring."""
    result = arg1 + arg2
    return result

# Bad
def myFunction(arg1,arg2):
  result=arg1+arg2
  return result
```

**Use Type Hints (Python 3.8+):**
```python
def process_data(data: str) -> dict:
    """Process data and return dict."""
    return {"result": data}
```

**Write Docstrings:**
```python
def my_command(self, arg):
    """
    Brief description of what the command does.
    
    Args:
        arg: Description of argument
    
    Returns:
        Description of return value
    """
    pass
```

---

### Command Implementation

When adding new commands, follow this template:

```python
def do_mycommand(self, arg):
    """Brief description for command list"""
    # Validate arguments
    if not arg:
        output().errmsg("Usage: mycommand <arg>")
        return
    
    # Implementation
    try:
        result = self.cmd(f"@PJL MYCOMMAND {arg}")
        if result:
            output().info(f"Success: {result}")
    except Exception as e:
        output().errmsg(f"Command failed: {e}")

def help_mycommand(self):
    """Show help for mycommand"""
    print()
    print("mycommand - Brief description")
    print("=" * 60)
    print("DESCRIPTION:")
    print("  Detailed description of what the command does.")
    print()
    print("USAGE:")
    print("  mycommand <arg>")
    print()
    print("EXAMPLES:")
    print("  mycommand test          # Example 1")
    print("  mycommand value         # Example 2")
    print()
    print("NOTES:")
    print("  - Important note 1")
    print("  - Important note 2")
    print()
```

---

### Testing Your Changes

```bash
# Test basic functionality
python3 printer-reaper.py --version

# Test discovery
python3 printer-reaper.py

# Test connection (use test printer!)
python3 printer-reaper.py <test-printer> pjl

# Test your new command
> mycommand test

# Test help
> help mycommand
```

---

## 📝 Commit Guidelines

### Commit Message Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:**
- `feat` - New feature
- `fix` - Bug fix
- `docs` - Documentation
- `style` - Formatting
- `refactor` - Code restructuring
- `test` - Adding tests
- `chore` - Maintenance

**Examples:**
```bash
feat(pjl): Add new mirror_async command for parallel mirroring

Implements asynchronous filesystem mirroring using ThreadPoolExecutor.
Significantly faster than sequential mirror on large filesystems.

- Added mirror_async command
- Implemented parallel download
- Updated help documentation
- Tested on HP LaserJet 4250

Closes #42

---

fix(discovery): Handle SNMP timeout gracefully

Fixed crash when SNMP times out during network scan.
Now displays warning and continues with next host.

Fixes #38

---

docs(wiki): Add troubleshooting guide for connection issues

Added comprehensive troubleshooting section covering:
- Connection refused errors
- Timeout issues
- Permission denied
- SNMP problems
```

---

## 🔍 Pull Request Process

### Before Submitting

**Checklist:**
- [ ] Code follows style guidelines
- [ ] All tests pass
- [ ] Help documentation added
- [ ] README updated (if needed)
- [ ] Changelog updated
- [ ] No linting errors
- [ ] Tested on test device

### Submitting PR

1. **Push to your fork:**
   ```bash
   git push origin feature/my-awesome-feature
   ```

2. **Create Pull Request on GitHub:**
   - Clear title
   - Detailed description
   - Link related issues
   - Add screenshots if applicable

3. **PR Template:**
   ```markdown
   ## Description
   Brief description of changes
   
   ## Type of Change
   - [ ] Bug fix
   - [ ] New feature
   - [ ] Documentation
   - [ ] Refactoring
   
   ## Testing
   - [ ] Tested on Linux
   - [ ] Tested on Windows
   - [ ] Tested on macOS
   - [ ] Tested on test printer
   
   ## Checklist
   - [ ] Code follows style guide
   - [ ] Help documentation added
   - [ ] Tests pass
   - [ ] Ready for review
   
   ## Related Issues
   Closes #42
   ```

### Review Process

1. Maintainer reviews code
2. Feedback provided (if needed)
3. You make changes
4. Re-review
5. Merge when approved

---

## 🧪 Testing Guidelines

### Manual Testing

```bash
# Test on multiple printers
python3 printer-reaper.py <hp-printer> pjl
python3 printer-reaper.py <brother-printer> pjl
python3 printer-reaper.py <epson-printer> pjl

# Test all affected commands
> mycommand test1
> mycommand test2
> mycommand edge_case
```

### Automated Testing (Future)

```python
# Unit tests (planned)
import unittest

class TestPJLCommands(unittest.TestCase):
    def test_upload_command(self):
        # Test implementation
        pass
```

---

## 📚 Documentation Guidelines

### Wiki Pages

When adding wiki pages:
- Use markdown format
- Include code examples
- Add navigation links
- Update sidebar

**Template:**
```markdown
# Page Title

Brief introduction.

---

## Section 1

Content...

## Section 2

Content...

---

<div align="center">

**Page Title**  
Brief tagline

**→ [Next Page](Next-Page)**

</div>
```

### Code Comments

```python
# Good comments explain WHY
def complex_function():
    # Use binary mode to preserve data integrity
    data = file().read(path)
    
    # HP printers require UEL before and after
    payload = c.UEL + command + c.UEL

# Avoid obvious comments
def simple_function():
    # Bad: Increment counter by 1
    counter = counter + 1
```

---

## 🎯 Priority Areas

### High Priority

1. **Parallel Network Scanning** - v2.3.5
2. **PostScript Module** - v2.4.0
3. **Export Functionality** - v2.3.5
4. **Enhanced Error Messages** - v2.3.5

### Medium Priority

1. **PCL Module** - v2.5.0
2. **Unit Tests** - Ongoing
3. **Performance Improvements** - Ongoing
4. **More Examples** - Ongoing

### Low Priority

1. **GUI Interface** - Future
2. **Web Dashboard** - Future
3. **Plugin System** - Future

---

## 🏆 Recognition

Contributors will be:
- Listed in CHANGELOG.md
- Mentioned in release notes
- Credited in commit messages
- Thanked in README.md

---

## 📞 Questions?

- **General Questions**: Open a discussion on GitHub
- **Bug Reports**: Open an issue
- **Feature Ideas**: Open a feature request
- **Direct Contact**: X / LinkedIn @mrhenrike

---

## 📖 Resources

### Helpful Links

- [Python cmd Module](https://docs.python.org/3/library/cmd.html)
- [PJL Technical Reference](http://h10032.www1.hp.com/ctg/Manual/bpl13208.pdf)
- [Hacking Printers Wiki](http://hacking-printers.net)
- [PEP 8 Style Guide](https://pep8.org/)

### Internal Documentation

- [Architecture](Architecture) - System design
- [Examples](Examples) - Code examples
- [PJL Commands](PJL-Commands) - Command reference

---

<div align="center">

**Contributing Guide**  
Thank you for contributing to PrinterReaper!

**→ [Back to Home](Home)**

</div>

