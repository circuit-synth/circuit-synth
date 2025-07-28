# Security Policy

## Supported Versions

We provide security updates for the following versions of Circuit-Synth:

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |
| < 0.1   | :x:                |

## Reporting a Vulnerability

We take the security of Circuit-Synth seriously. If you discover a security vulnerability, please report it to us as described below.

### How to Report

**Please do NOT report security vulnerabilities through public GitHub issues.**

Instead, please report security vulnerabilities by emailing: **security@circuitsynth.com**

You should receive a response within 48 hours. If for some reason you do not, please follow up via GitHub to ensure we received your original message.

### What to Include

Please include the following information in your report:

- **Type of issue**: (e.g., buffer overflow, SQL injection, cross-site scripting, etc.)
- **Full paths of source file(s)** related to the manifestation of the issue
- **Location of the affected source code** (tag/branch/commit or direct URL)
- **Special configuration required** to reproduce the issue
- **Step-by-step instructions** to reproduce the issue
- **Proof-of-concept or exploit code** (if possible)
- **Impact of the issue**, including how an attacker might exploit it

This information will help us triage your report more quickly.

## Security Considerations

### Input Validation

Circuit-Synth processes various types of input that could potentially be exploited:

- **KiCad schematic files** (.kicad_sch)
- **Netlist files** (.net)
- **JSON circuit definitions**
- **Python circuit definitions**
- **Symbol library files**

**Security measures in place**:
- Input validation on all file formats
- Sanitization of user-provided values
- Controlled file system access
- Memory-safe operations where possible

### File System Access

Circuit-Synth creates and modifies files on the local file system:

- **Generated KiCad projects**
- **Temporary files** during processing
- **Log files** and debug output
- **Cache files** for performance

**Security considerations**:
- Files are created only in user-specified directories
- No automatic execution of generated files
- Temporary files are cleaned up after use
- Log files don't contain sensitive information

### Code Execution

Circuit-Synth executes Python code in several contexts:

- **User-provided circuit definitions**
- **Plugin and extension code**
- **Template and generation scripts**

**Security measures**:
- No automatic execution of user-provided files
- Clear boundaries between user code and system operations
- No elevated privileges required for normal operation

### Network Access

Circuit-Synth may access network resources for:

- **Component library updates**
- **Documentation and examples**
- **Error reporting** (if enabled)

**Security considerations**:
- All network access is optional and user-controlled
- No automatic data transmission
- HTTPS used for all external communications
- No collection of personally identifiable information

## Known Security Limitations

### File System Permissions

Circuit-Synth requires write access to:
- Output directories for generated projects
- Temporary directories for processing
- Cache directories for performance

**User responsibility**: Ensure Circuit-Synth is run with appropriate file system permissions and in trusted directories.

### KiCad Integration

Circuit-Synth generates files that will be opened by KiCad:
- Schematic files may contain custom text and graphics
- PCB files may reference external libraries
- Symbol definitions may include arbitrary metadata

**User responsibility**: Review generated files before opening in KiCad, especially when processing untrusted input.

### Python Code Execution

Circuit-Synth is designed to execute user-provided Python code:
- Circuit definitions are Python scripts
- Custom components may include arbitrary code
- Extension modules have full Python access

**User responsibility**: Only run Circuit-Synth with trusted Python code and in appropriate security contexts.

## Security Best Practices

### For Users

1. **Run in isolated environments**: Use virtual environments or containers when processing untrusted circuit definitions
2. **Validate inputs**: Review circuit definitions and input files before processing
3. **Limit file system access**: Run Circuit-Synth in directories with appropriate permissions
4. **Keep updated**: Use the latest version with security patches
5. **Review outputs**: Inspect generated files before opening in KiCad

### For Developers

1. **Input validation**: Validate all external inputs thoroughly
2. **Safe file operations**: Use safe file handling practices
3. **Minimize privileges**: Don't require elevated permissions
4. **Secure defaults**: Use secure configurations by default
5. **Regular updates**: Keep dependencies updated

## Incident Response

If a security vulnerability is confirmed, we will:

1. **Acknowledge receipt** within 48 hours
2. **Investigate and confirm** the vulnerability
3. **Develop and test** a fix
4. **Coordinate disclosure** with the reporter
5. **Release a security update** as soon as possible
6. **Publish a security advisory** with details and mitigation steps

### Timeline Goals

- **Initial response**: Within 48 hours
- **Status update**: Within 1 week
- **Fix development**: Within 2 weeks (depending on complexity)
- **Security release**: As soon as fix is tested and validated

## Security Updates

Security updates will be:

- **Released immediately** for critical vulnerabilities
- **Clearly marked** in release notes
- **Backported** to supported versions when possible
- **Announced** through GitHub security advisories

## Contact Information

- **Security email**: security@circuitsynth.com
- **General contact**: Via GitHub issues (for non-security matters)
- **Project maintainer**: [@shanemattner](https://github.com/shanemattner)

## Attribution

We believe in coordinated disclosure and will credit security researchers who report vulnerabilities responsibly, unless they prefer to remain anonymous.

---

**Last Updated**: 2025-07-28  
**Version**: 1.0