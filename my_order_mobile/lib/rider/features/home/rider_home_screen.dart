import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/flavor_provider.dart';
import '../../../core/auth/user.dart';
import '../../../core/auth/auth_provider.dart';
import '../../../core/theme/spacing.dart';
import '../../../core/widgets/mo_card.dart';
import '../../../core/widgets/mo_feedback.dart';
import '../application/rider_apply_screen.dart';

/// Rider app home — a state machine per FLUTTER_DESIGN.md Section 3:
///   rider_status = none           -> R8 apply form
///   rider_status = pending_review -> R9 "under review"
///   rider_status = rejected       -> rejection notice + reapply
///   rider_status = approved       -> R1 dashboard
class RiderHomeScreen extends ConsumerWidget {
  const RiderHomeScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final auth = ref.watch(authProvider);
    final profile = auth.profile;

    // Safety net: the flavor role guard should catch non-riders earlier.
    if (profile == null || profile.role.name != 'rider') {
      return const Scaffold(body: Center(child: CircularProgressIndicator()));
    }

    return switch (profile.riderStatus) {
      'none' => const RiderApplyScreen(),
      'pending_review' => const _PendingView(),
      // Backend allows a new application once the old one is no longer
      // pending, so rejected riders can reapply from the form.
      'rejected' => _RejectedView(
          onReapply: () => Navigator.of(context).push(
                MaterialPageRoute(builder: (_) => const RiderApplyScreen()),
              ),
        ),
      'approved' => _RiderDashboard(profile: profile),
      _ => const RiderApplyScreen(),
    };
  }
}

/// R9 — shown while the admin has not yet reviewed the application.
class _PendingView extends ConsumerWidget {
  const _PendingView();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final config = ref.watch(flavorProvider);
    return _StatusScaffold(
      config: config,
      child: MOEmptyState(
        icon: Icons.hourglass_top_rounded,
        title: 'Application Under Review',
        message:
            'Your rider application is awaiting admin review.\n\n'
            'You will be able to receive orders once approved.',
        action: FilledButton.icon(
          onPressed: () => ref.read(authProvider.notifier).refreshProfile(),
          icon: const Icon(Icons.refresh),
          label: const Text('Check Status'),
        ),
      ),
    );
  }
}

/// Shown after an application was rejected; offers reapply.
class _RejectedView extends ConsumerWidget {
  final VoidCallback onReapply;
  const _RejectedView({required this.onReapply});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final config = ref.watch(flavorProvider);
    return _StatusScaffold(
      config: config,
      child: MOEmptyState(
        icon: Icons.cancel_outlined,
        title: 'Application Rejected',
        message:
            'Unfortunately your application was not approved.\n'
            'You may submit a new application.',
        action: FilledButton(
          onPressed: onReapply,
          child: const Text('Reapply'),
        ),
      ),
    );
  }
}

/// Shared scaffold for pending/rejected states.
class _StatusScaffold extends StatelessWidget {
  final dynamic config;
  final Widget child;
  const _StatusScaffold({required this.config, required this.child});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(config.appName),
        actions: const [_LogoutAction()],
      ),
      body: SafeArea(child: child),
    );
  }
}

/// R1 dashboard for approved riders (placeholder until Phase 3).
class _RiderDashboard extends ConsumerWidget {
  final UserProfile profile;
  const _RiderDashboard({required this.profile});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final theme = Theme.of(context);
    final config = ref.watch(flavorProvider);

    return Scaffold(
      appBar: AppBar(
        title: Text(config.appName),
        actions: const [_LogoutAction()],
      ),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(MOSpacing.lg),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              // Greeting + earnings placeholder
              Text('Hello, ${profile.name} 👋',
                  style: theme.textTheme.headlineMedium),
              Text('Ready to deliver',
                  style: theme.textTheme.bodyMedium),
              const SizedBox(height: MOSpacing.lg),

              // Today's summary card
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
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text('Approved & Active',
                        style: theme.textTheme.titleMedium?.copyWith(
                            color: Colors.white70)),
                    const SizedBox(height: MOSpacing.xs),
                    Text('0 MMK',
                        style: theme.textTheme.headlineMedium?.copyWith(
                            color: Colors.white, fontWeight: FontWeight.bold)),
                    Text('earned today',
                        style: theme.textTheme.bodySmall
                            ?.copyWith(color: Colors.white70)),
                  ],
                ),
              ),
              const SizedBox(height: MOSpacing.xl),

              const MOSectionHeader(
                title: 'Assigned Orders',
                subtitle: 'Orders assigned to you by admin',
              ),
              const SizedBox(height: MOSpacing.md),

              const MOEmptyState(
                icon: Icons.inbox_outlined,
                title: 'No assigned orders yet',
                message:
                    'Orders appear here once an admin assigns them to you.\n'
                    'The delivery flow arrives in Phase 3.',
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _LogoutAction extends ConsumerWidget {
  const _LogoutAction();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return IconButton(
      icon: const Icon(Icons.logout),
      tooltip: 'Logout',
      onPressed: () => ref.read(authProvider.notifier).logout(),
    );
  }
}
