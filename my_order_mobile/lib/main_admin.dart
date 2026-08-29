import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'core/app_config.dart';
import 'core/flavor_provider.dart';
import 'core/widgets/shared_auth_scaffold.dart';
import 'admin/features/dashboard/admin_dashboard_screen.dart';

void main() {
  runApp(
    ProviderScope(
      overrides: [
        flavorProvider.overrideWithValue(FlavorConfig.admin),
      ],
      child: const _AdminApp(),
    ),
  );
}

class _AdminApp extends ConsumerWidget {
  const _AdminApp();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final config = ref.watch(flavorProvider);
    return FlavorApp(
      config: config,
      homeBuilder: (context) => const AdminDashboardScreen(),
    );
  }
}