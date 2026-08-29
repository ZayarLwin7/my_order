import 'package:flutter/material.dart';

import '../theme/spacing.dart';

/// Empty-state widget for lists & screens.
class MOEmptyState extends StatelessWidget {
  final IconData icon;
  final String title;
  final String? message;
  final Widget? action;

  const MOEmptyState({
    super.key,
    required this.icon,
    required this.title,
    this.message,
    this.action,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(MOSpacing.xl),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Container(
              width: 88,
              height: 88,
              decoration: BoxDecoration(
                color: theme.colorScheme.primary.withValues(alpha: 0.08),
                shape: BoxShape.circle,
              ),
              child: Icon(icon, size: 40, color: theme.colorScheme.primary),
            ),
            const SizedBox(height: MOSpacing.lg),
            Text(title,
                style: theme.textTheme.titleMedium
                    ?.copyWith(fontWeight: FontWeight.w700),
                textAlign: TextAlign.center),
            if (message != null) ...[
              const SizedBox(height: MOSpacing.xs),
              Text(message!,
                  style: theme.textTheme.bodyMedium,
                  textAlign: TextAlign.center),
            ],
            if (action != null) ...[
              const SizedBox(height: MOSpacing.lg),
              action!,
            ],
          ],
        ),
      ),
    );
  }
}

/// Centered error state with retry.
class MOErrorView extends StatelessWidget {
  final String message;
  final VoidCallback? onRetry;

  const MOErrorView({super.key, required this.message, this.onRetry});

  @override
  Widget build(BuildContext context) {
    return MOEmptyState(
      icon: Icons.error_outline_rounded,
      title: 'Something went wrong',
      message: message,
      action: onRetry == null
          ? null
          : OutlinedButton.icon(
              onPressed: onRetry,
              icon: const Icon(Icons.refresh),
              label: const Text('Retry'),
            ),
    );
  }
}

/// Lightweight loading placeholder (circular) with message.
class MOLoadingView extends StatelessWidget {
  final String? message;

  const MOLoadingView({super.key, this.message});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Center(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          const CircularProgressIndicator(),
          if (message != null) ...[
            const SizedBox(height: MOSpacing.md),
            Text(message!, style: theme.textTheme.bodyMedium),
          ],
        ],
      ),
    );
  }
}

/// Simple app-wide success/error feedback helper.
void showMOSnack(BuildContext context, String message, {bool isError = false}) {
  ScaffoldMessenger.of(context)
    ..hideCurrentSnackBar()
    ..showSnackBar(
      SnackBar(
        content: Text(message),
        backgroundColor: isError
            ? Theme.of(context).colorScheme.error
            : null,
        duration: const Duration(seconds: 3),
      ),
    );
}
