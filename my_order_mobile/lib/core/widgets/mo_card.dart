import 'package:flutter/material.dart';

import '../theme/spacing.dart';

/// Consistent surface card used across the app.
class MOCard extends StatelessWidget {
  final Widget child;
  final EdgeInsetsGeometry padding;
  final VoidCallback? onTap;
  final bool emphasized;

  const MOCard({
    super.key,
    required this.child,
    this.padding = const EdgeInsets.all(MOSpacing.md),
    this.onTap,
    this.emphasized = false,
  });

  @override
  Widget build(BuildContext context) {
    final card = Card(
      color: emphasized ? Theme.of(context).colorScheme.primaryContainer : null,
      child: Padding(padding: padding, child: child),
    );
    if (onTap == null) return card;
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(MORadius.lg),
      child: card,
    );
  }
}

/// Section header with optional action.
class MOSectionHeader extends StatelessWidget {
  final String title;
  final String? subtitle;
  final Widget? trailing;

  const MOSectionHeader({
    super.key,
    required this.title,
    this.subtitle,
    this.trailing,
  });

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(title,
                  style: Theme.of(context)
                      .textTheme
                      .titleMedium
                      ?.copyWith(fontWeight: FontWeight.w700)),
              if (subtitle != null)
                Text(subtitle!,
                    style: Theme.of(context).textTheme.bodySmall),
            ],
          ),
        ),
        ?trailing,
      ],
    );
  }
}
