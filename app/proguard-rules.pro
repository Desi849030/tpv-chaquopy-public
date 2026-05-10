# TPV Ultra Smart — ProGuard Rules v2.3.0

# === Chaquopy (Python embebido) ===
-keep class com.chaquo.python.** { *; }
-dontwarn com.chaquo.python.**

# === Python runtime ===
-keep class org.python.** { *; }
-keep class jython.** { *; }

# === Flask y dependencias Python-Java bridge ===
-keep class flask.** { *; }
-keep class werkzeug.** { *; }
-keep class jinja2.** { *; }
-keep class markupsafe.** { *; }
-keep class click.** { *; }
-keep class itsdangerous.** { *; }
-keep class six.** { *; }

# === AndroidX ===
-keep class androidx.** { *; }
-keep interface androidx.** { *; }

# === Material Design ===
-keep class com.google.android.material.** { *; }
-keep class com.google.android.gms.** { *; }

# === WebView JavaScript Interface ===
-keepclassmembers class * {
    @android.webkit.JavascriptInterface <methods>;
}

# === Modelo de datos (JNI/Chaquopy access) ===
-keepclassmembers class * { <fields>; }

# === Enumeraciones ===
-keepclassmembers enum * {
    **[] values();
    public ** valueOf(java.lang.String);
}

# === Biometria ===
-keep class androidx.biometric.** { *; }

# === SQLCipher (si se integra) ===
-keep class net.sqlcipher.** { *; }
-keep class net.zetetic.database.** { *; }

# === OkHttp / Networking ===
-keep class okhttp3.** { *; }
-keep class okio.** { *; }
-dontwarn okhttp3.**
-dontwarn okio.**

# === Gson (si se usa) ===
-keep class com.google.gson.** { *; }
-keepattributes Signature
-keepattributes *Annotation*
-keep class com.tpv.pos.** { *; }

# === Serializacion ===
-keepclassmembers class * implements java.io.Serializable {
    static final long serialVersionUID;
    private static final java.io.ObjectStreamField[] serialPersistentFields;
    !static !transient <fields>;
    private void writeObject(java.io.ObjectOutputStream);
    private void readObject(java.io.ObjectInputStream);
    java.lang.Object writeReplace();
    java.lang.Object readResolve();
}

# === Removing warnings comunes ===
-dontwarn javax.annotation.**
-dontwarn kotlin.**
-dontwarn io.netty.**
-dontwarn org.conscrypt.**
