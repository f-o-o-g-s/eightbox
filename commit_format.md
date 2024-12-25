# Commit Message Quick Reference

## Basic Format
```
<type>: <description>
```

## Common Types
| Type | Use For | Example |
|------|---------|---------|
| `fix:` | Bug fixes | `fix: correct OTDL excusal handling` |
| `feat:` | New features | `feat: add carrier filtering` |
| `docs:` | Documentation | `docs: update README` |
| `style:` | Formatting | `style: fix indentation` |

## All Available Types
- `fix:` - Bug fixes
- `feat:` - New features
- `docs:` - Documentation changes
- `style:` - Code formatting
- `refactor:` - Code restructuring
- `perf:` - Performance improvements
- `test:` - Testing
- `build:` - Build system
- `ci:` - CI configuration
- `chore:` - Maintenance
- `revert:` - Reverting changes

## Advanced Formats

### Breaking Changes
Add `!` after the type:
```
feat!: completely redesign UI
```

### Scopes
Add context in parentheses:
```
fix(85g): correct OTDL excusal logic
feat(ui): add new filter buttons
docs(api): update function documentation
```

Common scopes in Eightbox:
- `ui` - User interface changes
- `85d`, `85f`, `85g` - Specific article violations
- `backup` - Backup system
- `db` - Database changes

## Quick Commands

### Backup Script
```bash
# Basic usage (adds fix: automatically)
python backup.py "description"

# With type
python backup.py "feat: new feature"

# With scope
python backup.py "fix(ui): correct button alignment"

# With ZIP backup
python backup.py --zip "docs: update README"
```

### Release Script
```bash
# Interactive mode
python release.py

# Non-interactive mode
python release.py --non-interactive \
    --type patch \
    --message "fix: bug fix" \
    --notes "Fixed bug" "Updated docs"
```

## Tips
1. If you forget the format, use:
   ```bash
   python backup.py --help
   ```

2. When in doubt, use `fix:` for small changes and `feat:` for new features

3. The pre-commit hook will show helpful examples if your format is incorrect

4. Both backup.py and release.py will add `fix:` automatically if you forget the type 