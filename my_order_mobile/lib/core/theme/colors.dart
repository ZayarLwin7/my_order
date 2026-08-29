import 'package:flutter/material.dart';

/// My-Order design system colors.
class MOColors {
  MOColors._();

  // Brand
  static const Color primary = Color(0xFF1A73E8);
  static const Color primaryDark = Color(0xFF0D47A1);
  static const Color accent = Color(0xFFFFB300);

  // Role identities
  static const Color senderColor = Color(0xFF2E7D32);
  static const Color riderColor = Color(0xFFEF6C00);
  static const Color staffColor = Color(0xFF6A1B9A);
  static const Color adminColor = Color(0xFF37474F);

  // Status colors
  static const Color statusPending = Color(0xFFF9A825);
  static const Color statusAssigned = Color(0xFF1E88E5);
  static const Color statusInTransit = Color(0xFF00897B);
  static const Color statusDelivered = Color(0xFF43A047);
  static const Color statusTerminal = Color(0xFF00ACC1);
  static const Color statusFailed = Color(0xFFE53935);
  static const Color statusDisputed = Color(0xFF8E24AA);
  static const Color statusCancelled = Color(0xFF757575);

  // Semantic
  static const Color error = Color(0xFFD32F2F);
  static const Color success = Color(0xFF2E7D32);
  static const Color warning = Color(0xFFF59E0B);

  // Surface tones
  static const Color surfaceLight = Color(0xFFF5F6FA);
  static const Color surfaceDark = Color(0xFF121212);
  static const Color cardLight = Colors.white;
  static const Color textPrimary = Color(0xFF1F2937);
  static const Color textSecondary = Color(0xFF6B7280);
  static const Color textHint = Color(0xFF9CA3AF);
  static const Color borderLight = Color(0xFFE5E7EB);
}