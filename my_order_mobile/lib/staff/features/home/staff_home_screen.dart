import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/flavor_provider.dart';
import '../../../core/auth/auth_provider.dart';
import '../../../core/theme/spacing.dart';
import '../../../core/widgets/mo_card.dart';
import '../../../core/widgets/mo_feedback.dart';

/// Staff app home (W1 placeholder — walk-in module in Phase 5).
class StaffHomeScreen extends ConsumerWidget {
  const StaffHomeScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final auth = ref.watch(authProvider);
    final config = ref.watch(flavorProvider);
    final theme = Theme.of(context);

    return Scaffold(
      appBar: AppBar(
        title: Text(config.appName),
        actions: [
          IconButton(
            icon: const Icon(Icons.logout),
            tooltip: 'Logout',
            onPressed: () => ref.read(authProvider.notifier).logout(),
          ),
        ],
      ),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(MOSpacing.lg),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Text('Hello, ${auth.profile?.name ?? ''} 👋',
                  style: theme.textTheme.headlineMedium),
              Text('Office operations', style: theme.textTheme.bodyMedium),
              const SizedBox(height: MOSpacing.lg),

              // Primary action (disabled until Phase 5)
              Container(
                padding: const EdgeInsets.all(MOSpacing.lg),
                decoration: BoxDecoration(
                  gradient: LinearGradient(
                    begin: Alignment.topLeft,
                    end: Alignment.bottomRight,
                    colors: [
                      config.brandColor,
                      config.brandColor.withValues(alpha: 0.75),
                    ],
                  ),
                  borderRadius: BorderRadius.circular(MORadius.xl),
                ),
                child: Row(
                  children: [
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text('New Walk-in Order',
                              style: theme.textTheme.titleLarge?.copyWith(
                                  color: Colors.white,
                                  fontWeight: FontWeight.bold)),
                          const SizedBox(height: MOSpacing.xxs),
                          Text('Create orders for customers without accounts',
                              style: theme.textTheme.bodyMedium
                                  ?.copyWith(color: Colors.white70)),
                        ],
                      ),
                    ),
                    Container(
                      width: 52,
                      height: 52,
                      decoration: BoxDecoration(
                        color: Colors.white.withValues(alpha: 0.2),
                        shape: BoxShape.circle,
                      ),
                      child: const Icon(Icons.add_rounded,
                          color: Colors.white, size: 28),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: MOSpacing.xl),

              const MOSectionHeader(
                title: 'Today',
                subtitle: 'Walk-in orders created by your office',
              ),
              const SizedBox(height: MOSpacing.md),

              const MOEmptyState(
                icon: Icons.storefront_outlined,
                title: 'No walk-in orders yet',
                message:
                    'The walk-in order module (W1–W5) arrives in Phase 5.\n'
                    'For now, staff accounts authenticate and land here.',
              ),
            ],
          ),
        ),
      ),
    );
  }
}
