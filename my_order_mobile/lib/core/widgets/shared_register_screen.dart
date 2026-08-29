import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../app_config.dart';
import '../utils/validators.dart';
import '../auth/user.dart';
import '../auth/auth_provider.dart';
import '../theme/spacing.dart';

/// Register screen for flavors that allow public signup.
/// Role is FIXED per flavor (never a user choice) — backend rejects
/// admin/staff self-registration regardless (PublicRegistrationRole).
class RegisterScreen extends ConsumerStatefulWidget {
  final FlavorConfig config;
  const RegisterScreen({super.key, required this.config});

  @override
  ConsumerState<RegisterScreen> createState() => _RegisterScreenState();
}

class _RegisterScreenState extends ConsumerState<RegisterScreen> {
  final _formKey = GlobalKey<FormState>();
  final _nameController = TextEditingController();
  final _phoneController = TextEditingController();
  final _passwordController = TextEditingController();
  bool _obscurePassword = true;
  bool _submitting = false;

  @override
  void dispose() {
    _nameController.dispose();
    _phoneController.dispose();
    _passwordController.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    if (!_formKey.currentState!.validate()) return;
    setState(() => _submitting = true);

    final error = await ref.read(authProvider.notifier).register(
          name: _nameController.text,
          phone: _phoneController.text,
          password: _passwordController.text,
          role: widget.config.flavor == AppFlavor.customer
              ? UserRole.sender
              : UserRole.rider,
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
              theme.scaffoldBackgroundColor,
            ],
          ),
        ),
        child: SafeArea(
          child: SingleChildScrollView(
            padding: const EdgeInsets.symmetric(
              horizontal: MOSpacing.lg,
              vertical: MOSpacing.lg,
            ),
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 420),
              child: Center(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    // Brand mark
                    Center(
                      child: Container(
                        width: 88,
                        height: 88,
                        decoration: BoxDecoration(
                          color: config.brandColor.withValues(alpha: 0.12),
                          shape: BoxShape.circle,
                        ),
                        child: Icon(config.icon,
                            size: 44, color: config.brandColor),
                      ),
                    ),
                    const SizedBox(height: MOSpacing.lg),
                    Text(
                      'Join ${config.appName}',
                      style: theme.textTheme.headlineMedium?.copyWith(
                        fontWeight: FontWeight.bold,
                        color: const Color(0xFF1F2937),
                      ),
                      textAlign: TextAlign.center,
                    ),
                    const SizedBox(height: MOSpacing.xs),
                    Text(
                      config.tagline,
                      textAlign: TextAlign.center,
                      style: theme.textTheme.bodyMedium,
                    ),
                    const SizedBox(height: MOSpacing.lg),
                    // Form card
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
                              controller: _nameController,
                              decoration: const InputDecoration(
                                labelText: 'Full name',
                                prefixIcon: Icon(Icons.person_outline_rounded),
                              ),
                              validator: Validators.name,
                              textInputAction: TextInputAction.next,
                            ),
                            const SizedBox(height: MOSpacing.md),
                            TextFormField(
                              controller: _phoneController,
                              decoration: const InputDecoration(
                                labelText: 'Phone number',
                                hintText: '09xxxxxxxxx',
                                prefixIcon: Icon(Icons.phone_android_rounded),
                              ),
                              keyboardType: TextInputType.phone,
                              validator: Validators.phone,
                              textInputAction: TextInputAction.next,
                            ),
                            const SizedBox(height: MOSpacing.md),
                            TextFormField(
                              controller: _passwordController,
                              obscureText: _obscurePassword,
                              decoration: InputDecoration(
                                labelText: 'Password',
                                helperText: 'At least 12 characters',
                                prefixIcon:
                                    const Icon(Icons.lock_outline_rounded),
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
                              ),
                              validator: Validators.password,
                              onFieldSubmitted: (_) => _submit(),
                            ),
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
                                onPressed: _submitting ? null : _submit,
                                child: _submitting
                                    ? const SizedBox(
                                        height: 22,
                                        width: 22,
                                        child: CircularProgressIndicator(
                                            strokeWidth: 2,
                                            color: Colors.white),
                                      )
                                    : const Text('Create Account',
                                        style: TextStyle(
                                            fontSize: 16,
                                            fontWeight: FontWeight.w600)),
                              ),
                            ),
                          ],
                        ),
                      ),
                    ),
                    const SizedBox(height: MOSpacing.md),
                    Row(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Text("Already have an account?",
                            style: theme.textTheme.bodyMedium),
                        TextButton(
                          onPressed: () => Navigator.of(context).pop(),
                          child: Text(
                            'Sign In',
                            style: TextStyle(
                                color: config.brandColor,
                                fontWeight: FontWeight.w600),
                          ),
                        ),
                      ],
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
