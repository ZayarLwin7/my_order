import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

export 'shared_login_screen.dart' show LoginScreen;

import '../app_config.dart';
import '../theme/theme.dart';
import '../auth/user.dart';
import '../auth/auth_provider.dart';
import 'shared_login_screen.dart';

/// Root widget shared by all three flavors. Builds the app with the flavor's
/// branding and routes to its home screen after login.
class FlavorApp extends ConsumerWidget {
  final FlavorConfig config;
  final Widget Function(BuildContext) homeBuilder;

  const FlavorApp({super.key, required this.config, required this.homeBuilder});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return MaterialApp(
      title: config.appName,
      debugShowCheckedModeBanner: false,
      theme: MOTheme.light(config.brandColor),
      darkTheme: MOTheme.dark(config.brandColor),
      home: _AuthGate(config: config, homeBuilder: homeBuilder),
    );
  }
}

/// Watches auth state; shows splash/login/register or the flavor home.
class _AuthGate extends ConsumerWidget {
  final FlavorConfig config;
  final Widget Function(BuildContext) homeBuilder;

  const _AuthGate({required this.config, required this.homeBuilder});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final auth = ref.watch(authProvider);

    return AnimatedSwitcher(
      duration: const Duration(milliseconds: 250),
      child: switch (auth.status) {
        AuthStatus.loading => SplashScreen(config: config),
        AuthStatus.unauthenticated => LoginScreen(config: config),
        AuthStatus.authenticated when !_roleAllowed(auth.profile!.role, config) =>
          WrongRoleScreen(config: config, actualRole: auth.profile!.role.name),
        AuthStatus.authenticated => homeBuilder(context),
      },
    );
  }

  bool _roleAllowed(UserRole role, FlavorConfig config) =>
      role.name == config.allowedRole;
}

/// Shown when an account logs into the wrong app (Section 1A role guard).
class WrongRoleScreen extends ConsumerWidget {
  final FlavorConfig config;
  final String actualRole;

  const WrongRoleScreen({super.key, required this.config, required this.actualRole});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final theme = Theme.of(context);
    return Scaffold(
      body: Center(
        child: Padding(
          padding: const EdgeInsets.all(32),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Icon(Icons.error_outline, size: 72, color: theme.colorScheme.error),
              const SizedBox(height: 24),
              Text('Wrong app', style: theme.textTheme.headlineSmall),
              const SizedBox(height: 12),
              Text(
                '${config.wrongRoleMessage}\n\n(Your account role: $actualRole)',
                textAlign: TextAlign.center,
                style: theme.textTheme.bodyLarge,
              ),
              const SizedBox(height: 32),
              OutlinedButton(
                onPressed: () async {
                  await ref.read(authProvider.notifier).logout();
                },
                child: const Text('Sign out'),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

/// Splash screen shared across flavors, parameterized by config.
class SplashScreen extends StatelessWidget {
  final FlavorConfig config;
  const SplashScreen({super.key, required this.config});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Scaffold(
      body: Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(config.icon, size: 80, color: config.brandColor),
            const SizedBox(height: 16),
            Text(
              config.appName,
              style: theme.textTheme.headlineMedium?.copyWith(fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 32),
            const CircularProgressIndicator(),
          ],
        ),
      ),
    );
  }
}
