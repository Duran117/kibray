#!/usr/bin/env python3
"""
Script to wrap all messages.* strings with gettext _() in core/views.py
"""
import re


def wrap_messages_in_file(filepath):
    """Wrap all messages.error/success/warning/info strings with _()"""
    with open(filepath, encoding='utf-8') as f:
        content = f.read()

    # Pattern to match messages.xxx(request, "string") or messages.xxx(request, f"string...")
    # We need to handle:
    # 1. Simple strings: messages.error(request, "text")
    # 2. F-strings: messages.error(request, f"text {var}")
    # 3. Multi-line strings

    # First, handle simple strings (non f-strings)
    pattern1 = r'messages\.(error|success|warning|info)\(request,\s*"([^"]+)"\)'
    def replacement1(match):
        method = match.group(1)
        text = match.group(2)
        return f'messages.{method}(request, _("{text}"))'

    content = re.sub(pattern1, replacement1, content)

    # Handle f-strings - convert to % formatting with _()
    # Pattern: messages.xxx(request, f"text {var} more")
    pattern2 = r'messages\.(error|success|warning|info)\(request,\s*f"([^"]+)"\)'
    def replacement2(match):
        method = match.group(1)
        fstring = match.group(2)

        # Convert {var} to %(var)s
        # This is a simple conversion - may need manual review for complex cases
        converted = fstring
        # Find all {xxx} patterns
        vars_found = re.findall(r'\{([^}]+)\}', fstring)
        for var in vars_found:
            # Handle expressions like {obj.id} or {len(photos)}
            clean_var = var.strip()
            # Use a safe var name
            if '.' in clean_var:
                var_name = clean_var.split('.')[-1]
            elif '(' in clean_var:
                var_name = 'value'
            else:
                var_name = clean_var

            converted = converted.replace('{' + var + '}', f'%({var_name})s', 1)

        return f'messages.{method}(request, _("{converted}") % {{{vars_found[0] if vars_found else ""}}})'

    # For now, let's just mark f-strings for manual review
    # They need more careful handling

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"Wrapped messages in {filepath}")
    print("Note: F-strings need manual review and conversion to % formatting")

if __name__ == '__main__':
    wrap_messages_in_file('/Users/jesus/Documents/kibray/core/views.py')
    print("\nDone! Please review the changes, especially f-strings.")
