import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/flavor_provider.dart';
import '../../../core/auth/auth_provider.dart';
import '../../../core/theme/spacing.dart';
import '../../../core/widgets/mo_feedback.dart';
import 'rider_application_provider.dart';

/// R8 — Rider application form (NRC, license, vehicle plate).
/// Shown after registration; mandatory before any delivery work.
class RiderApplyScreen extends ConsumerStatefulWidget {
  const RiderApplyScreen({super.key});

  @override
  ConsumerState<RiderApplyScreen> createState() => _RiderApplyScreenState();
}

class _RiderApplyScreenState extends ConsumerState<RiderApplyScreen> {
  final _formKey = GlobalKey<FormState>();
  final _nrcController = TextEditingController();
  final _licenseController = TextEditingController();
  final _plateController = TextEditingController();

  @override
  void dispose() {
    _nrcController.dispose();
    _licenseController.dispose();
    _plateController.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    if (!_formKey.currentState!.validate()) return;
    await ref.read(riderApplicationProvider.notifier).submit(
          nrc: _nrcController.text,
          licenseNumber: _licenseController.text,
          vehiclePlate: _plateController.text,
        );
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final config = ref.watch(flavorProvider);
    final appState = ref.watch(riderApplicationProvider);

    // Success -> show pending status (R9)
    if (appState.submitted) {
      return const RiderApplicationStatusScreen();
    }

    return Scaffold(
      appBar: AppBar(
        title: const Text('Rider Application'),
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
          child: Center(
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 420),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  Center(
                    child: Container(
                      width: 88,
                      height: 88,
                      decoration: BoxDecoration(
                        color: config.brandColor.withValues(alpha: 0.12),
                        shape: BoxShape.circle,
                      ),
                      child: Icon(Icons.badge_outlined,
                          size: 44, color: config.brandColor),
                    ),
                  ),
                  const SizedBox(height: MOSpacing.lg),
                  Text(
                    'Become a Rider',
                    style: theme.textTheme.headlineMedium,
                    textAlign: TextAlign.center,
                  ),
                  const SizedBox(height: MOSpacing.xs),
                  Text(
                    'Submit your details for verification.\n'
                    'Our team reviews within 1–2 working days.',
                    textAlign: TextAlign.center,
                    style: theme.textTheme.bodyMedium,
                  ),
                  const SizedBox(height: MOSpacing.lg),
                  Container(
                    padding: const EdgeInsets.all(MOSpacing.lg),
                    decoration: BoxDecoration(
                      color: theme.colorScheme.surface,
                      borderRadius: BorderRadius.circular(24),
                      boxShadow: [
                        BoxShadow(
                          color: Colors.black.withValues(alpha: 0.06),
                          offset: const Offset(0, 8),
                          blurRadius: 24,
                        ),
                      ],
                    ),
                    child: Form(
                      key: _formKey,
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.stretch,
                        children: [
                          TextFormField(
                            controller: _nrcController,
                            decoration: const InputDecoration(
                              labelText: 'NRC number',
                              hintText: 'e.g. 12/ABC(N)123456',
                              prefixIcon: Icon(Icons.credit_card_rounded),
                            ),
                            validator: (v) => (v == null || v.trim().isEmpty)
                                ? 'NRC is required'
                                : null,
                            textInputAction: TextInputAction.next,
                          ),
                          const SizedBox(height: MOSpacing.md),
                          TextFormField(
                            controller: _licenseController,
                            decoration: const InputDecoration(
                              labelText: 'Driving license number',
                              prefixIcon: Icon(Icons.card_membership_rounded),
                            ),
                            validator: (v) => (v == null || v.trim().isEmpty)
                                ? 'License number is required'
                                : null,
                            textInputAction: TextInputAction.next,
                          ),
                          const SizedBox(height: MOSpacing.md),
                          TextFormField(
                            controller: _plateController,
                            decoration: const InputDecoration(
                              labelText: 'Vehicle plate number',
                              hintText: 'e.g. YGN-1234',
                              prefixIcon: Icon(Icons.directions_bike_rounded),
                            ),
                            validator: (v) => (v == null || v.trim().isEmpty)
                                ? 'Vehicle plate is required'
                                : null,
                            textInputAction: TextInputAction.done,
                          ),
                          if (appState.error != null) ...[
                            const SizedBox(height: MOSpacing.md),
                            Text(
                              appState.error!,
                              style: TextStyle(
                                  color: theme.colorScheme.error,
                                  fontSize: 13),
                              textAlign: TextAlign.center,
                            ),
                          ],
                          const SizedBox(height: MOSpacing.lg),
                          SizedBox(
                            height: MOHeight.button,
                            child: FilledButton(
                              style: FilledButton.styleFrom(
                                backgroundColor: config.brandColor,
                                shape: RoundedRectangleBorder(
                                  borderRadius: BorderRadius.circular(14),
                                ),
                              ),
                              onPressed:
                                  appState.submitting ? null : _submit,
                              child: appState.submitting
                                  ? const SizedBox(
                                      height: 22,
                                      width: 22,
                                      child: CircularProgressIndicator(
                                          strokeWidth: 2, color: Colors.white),
                                    )
                                  : const Text('Submit Application'),
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}

/// R9 — Application status display after submission.
class RiderApplicationStatusScreen extends ConsumerWidget {
  const RiderApplicationStatusScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return Scaffold(
      body: SafeArea(
        child: MOEmptyState(
          icon: Icons.hourglass_top_rounded,
          title: 'Application Under Review',
          message:
              'Your rider application has been submitted and is awaiting '
              'admin review.\n\nYou will be able to receive orders once approved.',
          action: FilledButton.icon(
            onPressed: () =>
                ref.read(authProvider.notifier).refreshProfile(),
            icon: const Icon(Icons.refresh),
            label: const Text('Check Status'),
          ),
        ),
      ),
    );
  }
}
