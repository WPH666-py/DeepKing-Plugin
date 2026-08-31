package deepking.plugin

import com.intellij.openapi.project.Project
import com.intellij.openapi.wm.ToolWindow
import com.intellij.openapi.wm.ToolWindowFactory
import com.intellij.ui.content.ContentFactory
import com.intellij.ui.jcef.JBCefBrowser
import com.intellij.openapi.application.ApplicationManager
import com.intellij.openapi.diagnostic.Logger
import java.io.BufferedReader
import java.io.File
import java.io.InputStreamReader
import java.util.concurrent.TimeUnit

/**
 * DeepKing · AI 助手（JetBrains 侧边栏）
 *
 * 架构：Kotlin 插件仅做"壳"——
 *   1) 解包插件自带的 shared/core（node-host.js + webview/）到临时目录；
 *   2) 启动 `node node-host.js --port 0`（共享核心，与 VSCode 版同一份代码）；
 *   3) JCEF 面板加载 http://127.0.0.1:<port>/index.html?port=<port>（server 模式直连）。
 */
class DeepKingToolWindowFactory : ToolWindowFactory {

    override fun createToolWindowContent(project: Project, toolWindow: ToolWindow) {
        val browser = JBCefBrowser()
        val content = ContentFactory.getInstance().createContent(browser.component, "AI 助手", false)
        toolWindow.contentManager.addContent(content)
        // 异步拉起 Node 宿主后再导航（避免面板阻塞）
        ApplicationManager.getApplication().executeOnPooledThread {
            try {
                val res = extractResources()
                val port = startNodeHost(res)
                browser.loadURL("http://127.0.0.1:$port/index.html?port=$port")
            } catch (e: Exception) {
                LOG.error("DeepKing: 启动失败（请确认已安装 Node.js ≥ 18）", e)
                browser.loadHTML("<h3>DeepKing 启动失败</h3><p>${e.message}</p>")
            }
        }
    }

    /** 从插件 classpath 中取出 shared 资源（webview + node-host.js）到临时目录 */
    private fun extractResources(): File {
        val tmp = File(System.getProperty("java.io.tmpdir"), "deepking-plugin-runtime").apply { mkdirs() }
        val loader = javaClass.classLoader
        copyRes(loader, "/webview/index.html", File(tmp, "index.html"))
        copyRes(loader, "/webview/chat.js", File(tmp, "chat.js"))
        copyRes(loader, "/webview/style.css", File(tmp, "style.css"))
        copyRes(loader, "/webview/deepking.png", File(tmp, "deepking.png"))
        copyRes(loader, "/webview/node-host.js", File(tmp, "node-host.js"))
        return tmp
    }

    private fun copyRes(loader: ClassLoader, res: String, target: File) {
        loader.getResourceAsStream(res.removePrefix("/"))?.use { input ->
            target.outputStream().use { input.copyTo(it) }
        } ?: error("缺少资源 $res")
    }

    /** 启动 node-host（--port 0），从 stdout 读取服务端口 */
    private fun startNodeHost(dir: File): Int {
        val node = System.getenv("DEEPKING_NODE") ?: "node"
        val proc = ProcessBuilder(node, "node-host.js", "--port", "0")
            .directory(dir)
            .redirectErrorStream(false)
            .start()
        val reader = BufferedReader(InputStreamReader(proc.inputStream))
        repeat(30) {
            val line = reader.readLine() ?: error("node-host 提前退出")
            val m = Regex("listening on 127\\.0\\.0\\.1:(\\d+)").find(line)
            if (m != null) {
                sh(proc, reader) // 让 stdout 线程继续消费，避免阻塞子进程
                return m.groupValues[1].toInt()
            }
        }
        error("node-host 端口未就绪")
    }

    private fun sh(proc: Process, reader: BufferedReader) {
        Thread { try { reader.lines().forEach { } } catch (_: Exception) {} }.apply { isDaemon = true; start() }
    }

    companion object {
        private val LOG = Logger.getInstance(DeepKingToolWindowFactory::class.java)
    }
}
