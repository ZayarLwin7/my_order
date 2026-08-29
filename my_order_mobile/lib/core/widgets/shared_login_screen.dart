import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../app_config.dart';
import '../utils/validators.dart';
import '../auth/auth_provider.dart';
import 'shared_register_screen.dart';

/// Login screen shared by all flavors; branding + role guard from FlavorConfig.
class LoginScreen extends ConsumerStatefulWidget {
  final FlavorConfig config;
  const LoginScreen({super.key, required this.config});

  @override
  ConsumerState<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends ConsumerState<LoginScreen> {
  final _formKey = GlobalKey<FormState>();
  final _phoneController = TextEditingController();
  final _passwordController = TextEditingController();
  bool _obscurePassword = true;
  bool _submitting = false;

  @override
  void dispose() {
    _phoneController.dispose();
    _passwordController.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    if (!_formKey.currentState!.validate()) return;
    setState(() => _submitting = true);

    final error = await ref.read(authProvider.notifier).login(
          _phoneController.text,
          _passwordController.text,
        );

    if (!mounted) return;
    setState(() => _submitting = false);
    if (error != null) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(error),
          backgroundColor: Theme.of(context).colorScheme.error,
        ),
      );
    }
  }

  void _openRegister(BuildContext context) {
    Navigator.of(context).push(
      MaterialPageRoute(builder: (_) => RegisterScreen(config: widget.config)),
    );
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final config = widget.config;

    return Scaffold(
      body: Container(
        decoration: BoxDecoration(
          gradient: LinearGradient(
            begin: Alignment.topCenter,
            end: Alignment.bottomCenter,
            colors: [
              config.brandColor.withValues(alpha: 0.12),
              Colors.white,
              Colors.white,
            ],
          ),
        ),
        child: SafeArea(
          child: Center(
            child: SingleChildScrollView(
              padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 32),
              child: ConstrainedBox(
                constraints: const BoxConstraints(maxWidth: 420),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    // Brand mark
                    Center(
                      child: Container(
                        width: 96,
                        height: 96,
                        decoration: BoxDecoration(
                          color: config.brandColor.withValues(alpha: 0.12),
                          shape: BoxShape.circle,
                        ),
                        child: Icon(config.icon,
                            size: 48, color: config.brandColor),
                      ),
                    ),
                    const SizedBox(height: 20),
                    Text(
                      config.appName,
                      style: theme.textTheme.headlineMedium?.copyWith(
                        fontWeight: FontWeight.bold,
                        color: const Color(0xFF1F2937),
                      ),
                      textAlign: TextAlign.center,
                    ),
                    const SizedBox(height: 6),
                    Text(
                      config.tagline,
                      textAlign: TextAlign.center,
                      style: theme.textTheme.bodyMedium
                          ?.copyWith(color: const Color(0xFF6B7280)),
                    ),
                    const SizedBox(height: 32),
                    // Card
                    Container(
                      padding: const EdgeInsets.all(24),
                      decoration: BoxDecoration(
                        color: Colors.white,
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
                            Text(
                              'Welcome back',
                              style: theme.textTheme.titleLarge?.copyWith(
                                fontWeight: FontWeight.w600,
                                color: const Color(0xFF1F2937),
                              ),
                            ),
                            const SizedBox(height: 4),
                            Text(
                              'Sign in to continue',
                              style: theme.textTheme.bodyMedium
                                  ?.copyWith(color: const Color(0xFF9CA3AF)),
                            ),
                            const SizedBox(height: 24),
                            TextFormField(
                              controller: _phoneController,
                              decoration: InputDecoration(
                                labelText: 'Phone number',
                                hintText: '09xxxxxxxxx',
                                prefixIcon: const Icon(Icons.phone_android_outlined),
                                filled: true,
                                fillColor: const Color(0xFFF9FAFB),
                                border: OutlineInputBorder(
                                  borderRadius: BorderRadius.circular(14),
                                  borderSide: BorderSide.none,
                                ),
                                enabledBorder: OutlineInputBorder(
                                  borderRadius: BorderRadius.circular(14),
                                  borderSide: BorderSide.none,
                                ),
                                focusedBorder: OutlineInputBorder(
                                  borderRadius: BorderRadius.circular(14),
                                  borderSide: BorderSide(color: config.brandColor, width: 1.5),
                                ),
                              ),
                              keyboardType: TextInputType.phone,
                              validator: Validators.phone,
                              textInputAction: TextInputAction.next,
                            ),
                            const SizedBox(height: 16),
                            TextFormField(
                              controller: _passwordController,
                              obscureText: _obscurePassword,
                              decoration: InputDecoration(
                                labelText: 'Password',
                                prefixIcon: const Icon(Icons.lock_outline_rounded),
                                suffixIcon: IconButton(
                                  icon: Icon(
                                    _obscurePassword
                                        ? Icons.visibility_off_outlined
                                        : Icons.visibility_outlined,
                                    color: const Color(0xFF9CA3AF),
                                  ),
                                  onPressed: () => setState(
                                      () => _obscurePassword = !_obscurePassword),
                                ),
                                filled: true,
                                fillColor: const Color(0xFFF9FAFB),
                                border: OutlineInputBorder(
                                  borderRadius: BorderRadius.circular(14),
                                  borderSide: BorderSide.none,
                                ),
                                enabledBorder: OutlineInputBorder(
                                  borderRadius: BorderRadius.circular(14),
                                  borderSide: BorderSide.none,
                                ),
                                focusedBorder: OutlineInputBorder(
                                  borderRadius: BorderRadius.circular(14),
                                  borderSide: BorderSide(color: config.brandColor, width: 1.5),
                                ),
                              ),
                              validator: (v) => (v == null || v.isEmpty)
                                  ? 'Password is required'
                                  : null,
                              onFieldSubmitted: (_) => _submit(),
                            ),
                            const SizedBox(height: 24),
                            SizedBox(
                              height: 52,
                              child: FilledButton(
                                style: FilledButton.styleFrom(
                                  backgroundColor: config.brandColor,
                                  shape: RoundedRectangleBorder(
                                    borderRadius: BorderRadius.circular(14),
                                  ),
                                ),
                                onPressed: _submitting ? null : _submit,
                                child: _submitting
                                    ? const SizedBox(
                                        height: 22,
                                        width: 22,
                                        child: CircularProgressIndicator(
                                            strokeWidth: 2,
                                            color: Colors.white),
                                      )
                                    : const Text('Sign In',
                                        style: TextStyle(
                                            fontSize: 16,
                                            fontWeight: FontWeight.w600)),
                              ),
                            ),
                            // Public signup only in customer & rider apps.
                            if (config.flavor == AppFlavor.customer ||
                                config.flavor == AppFlavor.rider) ...[
                              const SizedBox(height: 20),
                              Row(
                                mainAxisAlignment: MainAxisAlignment.center,
                                children: [
                                  Text("Don't have an account?",
                                      style: TextStyle(
                                          color: const Color(0xFF6B7280),
                                          fontSize: 14)),
                                  TextButton(
                                    onPressed: () => _openRegister(context),
                                    child: Text(
                                      'Register',
                                      style: TextStyle(
                                          color: config.brandColor,
                                          fontWeight: FontWeight.w600),
                                    ),
                                  ),
                                ],
                              ),
                            ],
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
      ),
    );
  }
}
