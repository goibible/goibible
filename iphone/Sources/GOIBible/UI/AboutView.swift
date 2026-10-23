import SwiftUI

private let projectURL = URL(string: "https://goibible.org")!

private let mitLicense = """
MIT License

Copyright (c) 2026 Albert Yang

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""

struct AboutView: View {
    var body: some View {
        let version = Bundle.main.infoDictionary?["CFBundleShortVersionString"] as? String ?? "?"
        VStack(alignment: .leading, spacing: 0) {
            SheetHeader(title: "About")
            ScrollView {
                VStack(alignment: .leading, spacing: 12) {
                    Text("GOI Bible").font(.title.bold())
                    Text("Version \(version)").foregroundStyle(.secondary)
                    Text("Created by Albert Yang · © 2026")
                    Link(projectURL.absoluteString, destination: projectURL)
                    Divider()
                    Text("License").font(.headline)
                    Text(mitLicense).font(.caption).textSelection(.enabled)
                }
                .padding(16)
                .frame(maxWidth: .infinity, alignment: .leading)
            }
        }
    }
}
