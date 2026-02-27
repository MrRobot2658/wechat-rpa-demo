#!/usr/bin/env bash
# 编译并安装 Debug 包到已连接的真机（需 USB 调试已开启）
set -e
cd "$(dirname "$0")"

# 使用 JDK 17 以兼容 Gradle 8.4 + AGP 8.2（当前系统若为 Java 24 会不兼容）
if [ -z "$JAVA_HOME" ] || [[ "$(java -version 2>&1)" == *"24"* ]]; then
  if [ -d "/Applications/Android Studio.app/Contents/jbr/Contents/Home" ]; then
    export JAVA_HOME="/Applications/Android Studio.app/Contents/jbr/Contents/Home"
    echo "Using Android Studio JBR: $JAVA_HOME"
  elif command -v /usr/libexec/java_home &>/dev/null; then
    for v in 17 21 11; do
      if /usr/libexec/java_home -v "$v" 2>/dev/null; then
        export JAVA_HOME=$(/usr/libexec/java_home -v "$v")
        echo "Using JDK $v: $JAVA_HOME"
        break
      fi
    done
  fi
fi

if [ -z "$JAVA_HOME" ]; then
  echo "未检测到 JDK 17/21。请任选其一："
  echo "  1) 用 Android Studio 打开 android-app，选真机后点 Run"
  echo "  2) 安装 JDK 17 后执行: JAVA_HOME=\$(/usr/libexec/java_home -v 17) ./gradlew installDebug"
  exit 1
fi

./gradlew installDebug
