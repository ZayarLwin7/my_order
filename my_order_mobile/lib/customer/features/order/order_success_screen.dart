import 'package:flutter/material.dart';

import '../../../core/theme/spacing.dart';
import '../../../core/theme/colors.dart';
import '../../../core/utils/formatters.dart';

/// Phase 2 — P9 order-created success screen.
class OrderSuccessScreen extends StatelessWidget {
  final Map<String, dynamic> order;
  final String mode;
  const OrderSuccessScreen({super.key, required this.order, required this.mode});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final id = order['id']?.toString() ?? '-';
    final status = (order['status']?.toString() ?? 'pending').toUpperCase();
    final fee = (order['delivery_fee'] is num)
        ? Formatters.mmk((order['delivery_fee'] as num).toDouble())
        : (order['delivery_fee'] != null
            ? Formatters.mmk(num.tryParse(order['delivery_fee'].toString()) ?? 0.0)
            : '-');

    return Scaffold(
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(MOSpacing.xl),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Container(
                width: 96,
                height: 96,
                decoration: BoxDecoration(
                  color: MOColors.senderColor.withValues(alpha: 0.12),
                  shape: BoxShape.circle,
                ),
                child: const Icon(Icons.check_circle,
                    size: 56, color: MOColors.senderColor),
              ),
              const SizedBox(height: MOSpacing.lg),
              Text('Order created!',
                  style: theme.textTheme.headlineSmall
                      ?.copyWith(fontWeight: FontWeight.bold)),
              const SizedBox(height: MOSpacing.sm),
              Text('We\'ll assign a rider shortly.',
                  style: theme.textTheme.bodyMedium),
              const SizedBox(height: MOSpacing.xl),
              Container(
                width: double.infinity,
                padding: const EdgeInsets.all(MOSpacing.lg),
                decoration: BoxDecoration(
                  color: theme.colorScheme.surface,
                  borderRadius: BorderRadius.circular(16),
                  border: Border.all(color: theme.colorScheme.outlineVariant),
                ),
                child: Column(
                  children: [
                    _Row('Order ID', id),
                    _Row('Status', status),
                    _Row('Delivery fee', fee),
                    _Row('Mode',
                        mode == 'door_to_door' ? 'Door to Door' : 'Bus Terminal'),
                  ],
                ),
              ),
              const SizedBox(height: MOSpacing.xl),
              FilledButton(
                onPressed: () => Navigator.of(context)
                    .popUntil((route) => route.isFirst),
                style: FilledButton.styleFrom(
                  backgroundColor: MOColors.senderColor,
                  minimumSize: const Size.fromHeight(52),
                ),
                child: const Text('Back to home'),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _Row extends StatelessWidget {
  final String label;
  final String value;
  const _Row(this.label, this.value);

  @override
  Widget build(BuildContext context) => Padding(
        padding: const EdgeInsets.symmetric(vertical: MOSpacing.xs),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Text(label, style: Theme.of(context).textTheme.bodyMedium),
            Flexible(
              child: Text(value,
                  style: Theme.of(context)
                      .textTheme
                      .titleMedium
                      ?.copyWith(fontWeight: FontWeight.w600),
                  textAlign: TextAlign.right),
            ),
          ],
        ),
      );
}
