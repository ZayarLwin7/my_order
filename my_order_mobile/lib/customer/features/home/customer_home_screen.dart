import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/flavor_provider.dart';
import '../../../core/auth/auth_provider.dart';
import '../../../core/auth/user.dart';
import '../../../core/theme/spacing.dart';
import '../../../core/widgets/mo_card.dart';
import '../order/create_order_wizard.dart';

/// Customer app home (P1).
class CustomerHomeScreen extends ConsumerWidget {
  const CustomerHomeScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final auth = ref.watch(authProvider);
    final config = ref.watch(flavorProvider);
    final theme = Theme.of(context);
    final profile = auth.profile;

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
              // Greeting
              Text(
                'Hello, ${_firstName(profile?.name ?? '')} 👋',
                style: theme.textTheme.headlineMedium,
              ),
              Text(
                profile?.role == UserRole.sender && (profile?.isActivePartner ?? false)
                    ? 'Send with COD & partner benefits'
                    : 'What would you like to send today?',
                style: theme.textTheme.bodyMedium,
              ),
              const SizedBox(height: MOSpacing.lg),

              // Partner status banner (merchant features, Section 14)
              if (profile?.role == UserRole.sender)
                _PartnerBanner(profile: profile),

              const SizedBox(height: MOSpacing.lg),

              // Primary action card
              _NewOrderCard(
                brandColor: config.brandColor,
                onTap: () => Navigator.of(context).push(
                  MaterialPageRoute(
                    builder: (_) => const CreateOrderWizard(),
                  ),
                ),
              ),

              const SizedBox(height: MOSpacing.xl),

              const MOSectionHeader(
                title: 'Recent Orders',
                subtitle: 'Your latest deliveries',
              ),
              const SizedBox(height: MOSpacing.md),

              // Placeholder until Phase 2 order flow.
              const MOCard(
                child: Column(
                  children: [
                    _FeatureItem(
                      icon: Icons.local_shipping_outlined,
                      title: 'Order creation wizard',
                      subtitle: 'Coming in Phase 2 — send parcels with a few taps.',
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  String _firstName(String name) {
    final parts = name.trim().split(RegExp(r'\s+'));
    return parts.isNotEmpty ? parts.first : name;
  }
}

/// Merchant/partner status card shown to senders.
class _PartnerBanner extends StatelessWidget {
  final dynamic profile;
  const _PartnerBanner({required this.profile});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final status = (profile.partnerStatus ?? 'none') as String;

    final (icon, color, title, subtitle) = switch (status) {
      'approved' => (
          Icons.verified_outlined,
          theme.colorScheme.primary,
          'Merchant Account Active',
          'COD orders & settlements enabled',
        ),
      'pending_review' => (
          Icons.hourglass_top_rounded,
          Colors.amber.shade700,
          'Merchant Application Pending',
          'Our team is reviewing your application',
        ),
      'rejected' => (
          Icons.cancel_outlined,
          theme.colorScheme.error,
          'Merchant Application Rejected',
          'You can submit a new application',
        ),
      _ => (
          Icons.storefront_outlined,
          theme.colorScheme.secondary,
          'Become a Merchant',
          'Accept COD orders & track settlements',
        ),
    };

    return Container(
      padding: const EdgeInsets.all(MOSpacing.md),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.08),
        borderRadius: BorderRadius.circular(MORadius.md),
        border: Border.all(color: color.withValues(alpha: 0.25)),
      ),
      child: Row(
        children: [
          Icon(icon, color: color, size: 28),
          const SizedBox(width: MOSpacing.sm),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(title,
                    style: theme.textTheme.titleMedium
                        ?.copyWith(fontWeight: FontWeight.w600)),
                Text(subtitle, style: theme.textTheme.bodySmall),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

/// Big "New Order" action card.
class _NewOrderCard extends StatelessWidget {
  final Color brandColor;
  final VoidCallback onTap;
  const _NewOrderCard({required this.brandColor, required this.onTap});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(MORadius.xl),
      child: Container(
      padding: const EdgeInsets.all(MOSpacing.lg),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: [brandColor, brandColor.withValues(alpha: 0.75)],
        ),
        borderRadius: BorderRadius.circular(MORadius.xl),
      ),
      child: Row(
        children: [
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text('Send a parcel',
                    style: theme.textTheme.titleLarge?.copyWith(
                        color: Colors.white, fontWeight: FontWeight.bold)),
                const SizedBox(height: MOSpacing.xxs),
                Text('Door-to-door or bus terminal delivery',
                    style: theme.textTheme.bodyMedium
                        ?.copyWith(color: Colors.white70)),
              ],
            ),
          ),
          Container(
            width: 56,
            height: 56,
            decoration: BoxDecoration(
              color: Colors.white.withValues(alpha: 0.2),
              shape: BoxShape.circle,
            ),
            child: const Icon(Icons.arrow_forward_rounded,
                color: Colors.white, size: 30),
          ),
        ],
      ),
      ),
    );
  }
}

/// Simple feature list item.
class _FeatureItem extends StatelessWidget {
  final IconData icon;
  final String title;
  final String subtitle;
  const _FeatureItem({
    required this.icon,
    required this.title,
    required this.subtitle,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Row(
      children: [
        Container(
          width: 44,
          height: 44,
          decoration: BoxDecoration(
            color: theme.colorScheme.primary.withValues(alpha: 0.1),
            borderRadius: BorderRadius.circular(MORadius.sm),
          ),
          child: Icon(icon, color: theme.colorScheme.primary, size: 22),
        ),
        const SizedBox(width: MOSpacing.md),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(title, style: theme.textTheme.titleMedium),
              Text(subtitle, style: theme.textTheme.bodySmall),
            ],
          ),
        ),
      ],
    );
  }
}
