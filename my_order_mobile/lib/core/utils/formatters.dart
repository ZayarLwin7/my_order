import 'package:intl/intl.dart';

/// Formatting helpers for currency, phone, and dates.
class Formatters {
  Formatters._();

  static final NumberFormat _mmk = NumberFormat.decimalPattern();

  /// 5000 -> "5,000 MMK"
  static String mmk(num amount) => '${_mmk.format(amount)} MMK';

  /// ISO datetime -> "24 Aug 2026, 14:30"
  static String dateTime(String? iso) {
    if (iso == null || iso.isEmpty) return '-';
    final dt = DateTime.tryParse(iso);
    if (dt == null) return '-';
    return DateFormat('d MMM yyyy, HH:mm').format(dt.toLocal());
  }

  /// Masks a phone: "09777777777" -> "09*****7777"
  static String maskPhone(String phone) {
    if (phone.length < 8) return phone;
    return '${phone.substring(0, 2)}${'*' * (phone.length - 6)}${phone.substring(phone.length - 4)}';
  }
}
