import 'package:flutter/material.dart';

/// Design system spacing scale (8px grid).
class MOSpacing {
  MOSpacing._();

  static const double xxs = 4;
  static const double xs = 8;
  static const double sm = 12;
  static const double md = 16;
  static const double lg = 24;
  static const double xl = 32;
  static const double xxl = 48;

  static const EdgeInsets allXs = EdgeInsets.all(xs);
  static const EdgeInsets allSm = EdgeInsets.all(sm);
  static const EdgeInsets allMd = EdgeInsets.all(md);
  static const EdgeInsets allLg = EdgeInsets.all(lg);

  static const EdgeInsets hMd = EdgeInsets.symmetric(horizontal: md);
  static const EdgeInsets hLg = EdgeInsets.symmetric(horizontal: lg);

  static const EdgeInsets vSm = EdgeInsets.symmetric(vertical: sm);
  static const EdgeInsets vMd = EdgeInsets.symmetric(vertical: md);
}

/// Border radius scale.
class MORadius {
  MORadius._();

  static const double sm = 10;
  static const double md = 14;
  static const double lg = 20;
  static const double xl = 28;
  static const double full = 100;
}

/// Component heights.
class MOHeight {
  MOHeight._();

  static const double button = 52;
  static const double input = 56;
  static const double appBar = 64;
  static const double chip = 32;
}
