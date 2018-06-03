FILENAME = 'foo.c'
FILENAME_ALT = 'bar.c'

CODE = '''\
int main() {
  if (a) {
  return a;
  }
  return 0;
}
'''

FIXED = '''\
int main() {
  if (a) {
    return a;
  }
  return 0;
}
'''

FIXED_WEBKIT = '''\
int main()
{
    if (a) {
        return a;
    }
    return 0;
}
'''

FIXED_COMMIT = '''\
--- /dev/null
+++ b/foo.c
@@ ... @@
+int main() {
+  if (a) {
+    return a;
+  }
+  return 0;
+}
'''

NON_FIXED_COMMIT = '''\
--- /dev/null
+++ b/foo.c
@@ ... @@
+int main() {
+  if (a) {
+  return a;
+  }
+  return 0;
+}
'''

PATCH = '''\
--- foo.c	(before formatting)
+++ foo.c	(after formatting)
@@ ... @@
-  return a;
+    return a;
'''

PATCH_WEBKIT = '''\
--- foo.c	(before formatting)
+++ foo.c	(after formatting)
@@ ... @@
-int main() {
-  if (a) {
-  return a;
-  }
-  return 0;
+int main()
+{
+    if (a) {
+        return a;
+    }
+    return 0;
'''

PATCH_LLVM_INDENT8 = '''\
--- foo.c	(before formatting)
+++ foo.c	(after formatting)
@@ ... @@
-  if (a) {
-  return a;
-  }
-  return 0;
+        if (a) {
+                return a;
+        }
+        return 0;
'''

MODIFIED = CODE + '''\

static void foo() {
bar();
baz();
}
'''

MODIFIED_PART_PATCH = '''\
--- foo.c	(before formatting)
+++ foo.c	(after formatting)
@@ ... @@
-bar();
-baz();
+  bar();
+  baz();
'''
