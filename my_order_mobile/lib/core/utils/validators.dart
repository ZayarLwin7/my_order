/// Input validation helpers matching backend rules.
class Validators {
  Validators._();

  /// Myanmar phone: digits/spaces/dashes, starts with digit or +.
  /// Backend pattern: ^\+?[0-9][0-9 -]*$ with length 6..32
  static String? phone(String? value) {
    if (value == null || value.trim().isEmpty) return 'Phone number is required';
    final v = value.trim();
    if (v.length < 6 || v.length > 32) return 'Phone must be 6-32 characters';
    if (!RegExp(r'^\+?[0-9][0-9 -]*$').hasMatch(v)) {
      return 'Enter a valid phone number (digits only)';
    }
    return null;
  }

  /// Backend: password min 12 chars (registration), max 72.
  static String? password(String? value) {
    if (value == null || value.isEmpty) return 'Password is required';
    if (value.length < 12) return 'Password must be at least 12 characters';
    if (value.length > 72) return 'Password is too long';
    return null;
  }

  static String? name(String? value) {
    if (value == null || value.trim().isEmpty) return 'Name is required';
    if (value.trim().length > 100) return 'Name is too long';
    return null;
  }
}
