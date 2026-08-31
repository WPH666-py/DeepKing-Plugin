# DeepKing-Plugin · PyCharm / WebStorm 插件（JetBrains）
# 由 IntelliJ Platform Gradle 插件构建：./gradlew buildPlugin → build/distributions/*.zip → IDE 安装

plugins {
    id("java")
    id("org.jetbrains.intellij") version "1.17.4"
}

group = "com.wp666"
version = "0.1.0"

repositories { mavenCentral() }

intellij {
    version.set("2023.2")
    type.set("IC")   # PyCharm/WebStorm 兼容：安装时需先建对应版本的 plugin（也可改型为 PY/WS 分别构建）
    plugins.set(listOf("com.intellij.java"))
}

dependencies {
    implementation(files(layout.projectDirectory.dir("libs").asFile.listFiles().orEmpty())) // 无外部依赖
}

tasks {
    // 将共享核心（Node 宿主 + Web UI）拷入插件资源，随包分发
    processResources {
        doFirst {
            val shared = rootProject.projectDir.parentFile.resolve("shared")
            val res = destinationDir.resolve("webview")
            res.deleteRecursively()
            copy {
                from(File(shared, "webview").listFiles().orEmpty())
                into(res)
            }
            copy {
                from(File(shared, "node-host.js"))
                into(res)
            }
        }
    }
    patchPluginXml {
        sinceBuild.set("232")
        untilBuild.set("263.*")
    }
}

java {
    toolchain { languageVersion.set(JavaLanguageVersion.of(17)) }
}
