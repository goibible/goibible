import SwiftUI
import UniformTypeIdentifiers

private let downloadManifestURL =
    URL(string: "https://raw.githubusercontent.com/goibible/goibible/main/Meta_Bible_Data/goi_db_download/manifest.json")!
private let downloadBaseURL =
    URL(string: "https://raw.githubusercontent.com/goibible/goibible/main/Meta_Bible_Data/goi_db_download/")!

private struct DownloadEdition: Identifiable {
    let editionId: String
    let displayName: String
    let bcp47Tag: String
    let file: String
    let verseCount: Int
    var id: String { editionId }
}

/// Display settings + manage editions: list installed, merge a new one from a .db file
/// or by downloading, remove ones you no longer want.
struct SettingsView: View {
    let state: AppState
    @State private var status = ""
    @State private var busy = false
    @State private var url = ""
    @State private var downloadChoices: [DownloadEdition] = []
    @State private var showDownloadPicker = false
    @State private var showFileImporter = false
    @State private var removeTarget: Edition?
    @State private var showRemovePicker = false
    @State private var showResult = false

    var body: some View {
        VStack(spacing: 0) {
            SheetHeader(title: "Settings")
            Form {
                Section("Display") {
                    Toggle("Dark mode", isOn: Binding(get: { state.darkMode }, set: { state.updateDarkMode($0) }))
                    Picker("Font", selection: Binding(get: { state.fontKey }, set: { state.updateFont($0) })) {
                        ForEach(fontChoices, id: \.key) { Text($0.name).tag($0.key) }
                    }
                    .pickerStyle(.segmented)
                    HStack {
                        Text("Size \(state.fontSize)")
                        Slider(
                            value: Binding(get: { Double(state.fontSize) }, set: { state.updateFontSize(Int($0)) }),
                            in: 10...28, step: 1)
                    }
                    Text("In the beginning God created the heavens and the earth.")
                        .font(readerFont(state.fontKey, size: CGFloat(state.fontSize)))
                        .lineSpacing(CGFloat(state.fontSize) * 0.6)
                }

                Section("Editions") {
                    Button("Remove a Bible translation") { showRemovePicker = true }
                        .disabled(busy || state.editions.count <= 1)
                    ForEach(state.editions) { e in
                        HStack {
                            VStack(alignment: .leading) {
                                Text(e.displayName)
                                Text("\(e.id) · \(e.language)").font(.caption).foregroundStyle(.secondary)
                            }
                            Spacer()
                            Button { removeTarget = e } label: { Image(systemName: "trash") }
                                .buttonStyle(.borderless)
                                .disabled(state.editions.count <= 1 || busy)
                                .accessibilityLabel("Remove \(e.displayName)")
                        }
                    }
                    if state.editions.count == 1 {
                        Text("Keep at least one Bible translation installed.").font(.caption)
                    }
                }

                Section("Add edition") {
                    Button("Pick .db file from storage") { showFileImporter = true }.disabled(busy)
                    Button("Download .db") { Task { await loadDownloadChoices() } }.disabled(busy)
                    HStack {
                        TextField("Download URL (.db)", text: $url)
                            .autocorrectionDisabled()
                        Button("Get") { Task { await download(url, label: "download") } }
                            .disabled(busy || url.trimmingCharacters(in: .whitespaces).isEmpty)
                    }
                    if !status.isEmpty { Text(status).foregroundStyle(Theme.primary) }
                }
            }
            .formStyle(.grouped)
        }
        // Same as Android: a blocking progress overlay while busy, then a result dialog.
        .overlay {
            if busy {
                VStack(spacing: 16) {
                    Text("Bible translation").font(.headline)
                    ProgressView()
                    Text(status)
                }
                .padding(24)
                .background(.regularMaterial, in: RoundedRectangle(cornerRadius: 16))
            }
        }
        .onChange(of: busy) { _, nowBusy in
            if !nowBusy && !status.isEmpty { showResult = true }
        }
        .alert("Translation result", isPresented: $showResult) {
            Button("OK") { status = "" }
        } message: { Text(status) }
        .confirmationDialog("Remove a Bible translation", isPresented: $showRemovePicker, titleVisibility: .visible) {
            ForEach(state.editions) { e in
                Button(e.displayName) { removeTarget = e }
            }
            Button("Cancel", role: .cancel) {}
        }
        .fileImporter(isPresented: $showFileImporter, allowedContentTypes: [.data, .item]) { result in
            guard case .success(let picked) = result else { return }
            Task { await importFile(picked) }
        }
        .confirmationDialog("Download .db", isPresented: $showDownloadPicker, titleVisibility: .visible) {
            ForEach(downloadChoices) { d in
                Button("\(d.displayName) · \(d.bcp47Tag) · \(d.verseCount) verses") {
                    Task { await download(downloadBaseURL.appendingPathComponent(d.file).absoluteString, label: d.displayName) }
                }
            }
            Button("Cancel", role: .cancel) {}
        }
        .alert(
            "Remove \(removeTarget?.displayName ?? "")?",
            isPresented: Binding(get: { removeTarget != nil }, set: { if !$0 { removeTarget = nil } }),
            presenting: removeTarget
        ) { edition in
            Button("Remove", role: .destructive) { Task { await remove(edition) } }
            Button("Cancel", role: .cancel) {}
        } message: { _ in
            Text("This removes the translation and its bookmarks from this device. You can download it again later.")
        }
    }

    private func merge(_ file: URL) async {
        status = "Installing…"
        let repo = state.repo
        let result = await Task.detached { repo.mergeFrom(file) }.value
        try? FileManager.default.removeItem(at: file)
        switch result {
        case .success(let names): state.refreshEditions(); status = "Added: \(names)"
        case .failure(let e): status = "Failed: \(e.localizedDescription)"
        }
    }

    private func importFile(_ picked: URL) async {
        busy = true
        defer { busy = false }
        status = "Copying file…"
        let scoped = picked.startAccessingSecurityScopedResource()
        defer { if scoped { picked.stopAccessingSecurityScopedResource() } }
        let tmp = FileManager.default.temporaryDirectory.appendingPathComponent("import.db")
        do {
            try? FileManager.default.removeItem(at: tmp)
            try FileManager.default.copyItem(at: picked, to: tmp)
        } catch {
            status = "Could not read file"
            return
        }
        await merge(tmp)
    }

    private func download(_ target: String, label: String) async {
        guard let remote = URL(string: target.trimmingCharacters(in: .whitespaces)) else { return }
        busy = true
        defer { busy = false }
        status = "Downloading \(label)…"
        do {
            let (downloaded, _) = try await URLSession.shared.download(from: remote)
            let tmp = FileManager.default.temporaryDirectory.appendingPathComponent("download.db")
            try? FileManager.default.removeItem(at: tmp)
            try FileManager.default.moveItem(at: downloaded, to: tmp)
            await merge(tmp)
        } catch {
            status = "Download failed: \(error.localizedDescription)"
        }
    }

    private func loadDownloadChoices() async {
        busy = true
        defer { busy = false }
        status = "Loading downloads…"
        do {
            let (data, _) = try await URLSession.shared.data(from: downloadManifestURL)
            let json = try JSONSerialization.jsonObject(with: data) as? [String: Any]
            let items = json?["editions"] as? [[String: Any]] ?? []
            downloadChoices = items.compactMap { item in
                guard let id = item["edition_id"] as? String, let file = item["file"] as? String else { return nil }
                return DownloadEdition(
                    editionId: id,
                    displayName: item["display_name"] as? String ?? id,
                    bcp47Tag: item["bcp47_tag"] as? String ?? item["language_subtag"] as? String ?? "",
                    file: file,
                    verseCount: item["verse_count"] as? Int ?? 0)
            }
            status = downloadChoices.isEmpty ? "No downloads available." : ""
            showDownloadPicker = !downloadChoices.isEmpty
        } catch {
            status = "Could not load downloads: \(error.localizedDescription)"
        }
    }

    private func remove(_ edition: Edition) async {
        busy = true
        defer { busy = false }
        status = "Removing \(edition.displayName)…"
        let repo = state.repo
        do {
            try await Task.detached { try repo.removeEdition(edition.id) }.value
            state.refreshEditions()
            status = "Removed \(edition.displayName)"
        } catch {
            status = "Remove failed: \(error.localizedDescription)"
        }
    }
}
