// Native x64 Explorer extension. No Python or image decoding in Explorer.
#define UNICODE
#define _UNICODE
#include <windows.h>
#include <shlobj.h>
#include <shellapi.h>
#include <algorithm>
#include <atomic>
#include <cwctype>
#include <cstring>
#include <new>
#include <string>
#include <vector>

// {2B414F21-4B8D-4DB6-9E69-7EE68D08C822}
const CLSID CLSID_ConvertImage = {0x2b414f21,0x4b8d,0x4db6,{0x9e,0x69,0x7e,0xe6,0x8d,0x08,0xc8,0x22}};
static HMODULE moduleHandle;
static std::atomic<long> objects{0};
static const wchar_t* formats[] = {L"Avif", L"Jpg", L"Pdf", L"Png", L"Webp"};
static const wchar_t* presets[] = {L"High Quality", L"Standard", L"Small Size"};
static const char* formatIds[] = {"avif", "jpg", "pdf", "png", "webp"};
static const char* presetIds[] = {"high", "standard", "small"};

static bool supported(const std::wstring& path) {
    auto dot = path.find_last_of(L'.');
    if (dot == std::wstring::npos) return false;
    auto ext = path.substr(dot);
    std::transform(ext.begin(), ext.end(), ext.begin(), towlower);
    DWORD attr = GetFileAttributesW(path.c_str());
    return attr != INVALID_FILE_ATTRIBUTES && !(attr & FILE_ATTRIBUTE_DIRECTORY) &&
        (ext == L".jpg" || ext == L".jpeg" || ext == L".png" || ext == L".webp" || ext == L".avif");
}

static std::vector<std::wstring> readDrop(HDROP drop) {
    std::vector<std::wstring> paths;
    UINT count = DragQueryFileW(drop, 0xffffffff, nullptr, 0);
    for (UINT i = 0; i < count; ++i) {
        UINT len = DragQueryFileW(drop, i, nullptr, 0);
        std::wstring path(len + 1, L'\0');
        if (!DragQueryFileW(drop, i, path.data(), len + 1)) return {};
        path.resize(len);
        if (!supported(path)) return {};
        paths.push_back(path);
    }
    return paths;
}

static std::string jsonString(const std::wstring& value) {
    int size = WideCharToMultiByte(CP_UTF8, WC_ERR_INVALID_CHARS, value.data(), (int)value.size(), nullptr, 0, nullptr, nullptr);
    if (!size && !value.empty()) return {};
    std::string utf8(size, '\0'), result = "\"";
    WideCharToMultiByte(CP_UTF8, WC_ERR_INVALID_CHARS, value.data(), (int)value.size(), utf8.data(), size, nullptr, nullptr);
    const char hex[] = "0123456789abcdef";
    for (unsigned char c : utf8) {
        if (c == '"' || c == '\\') { result += '\\'; result += c; }
        else if (c < 32) { result += "\\u00"; result += hex[c >> 4]; result += hex[c & 15]; }
        else result += c;
    }
    return result + "\"";
}

static HRESULT buildMenu(HMENU menu, UINT position, UINT first, UINT last) {
    if (last < first || last - first < 14) return E_FAIL;
    HMENU root = CreatePopupMenu();
    if (!root) return E_OUTOFMEMORY;
    for (UINT f = 0; f < 5; ++f) {
        HMENU quality = CreatePopupMenu();
        if (!quality) { DestroyMenu(root); return E_OUTOFMEMORY; }
        for (UINT p = 0; p < 3; ++p)
            AppendMenuW(quality, MF_STRING, first + f * 3 + p, presets[p]);
        AppendMenuW(root, MF_POPUP, (UINT_PTR)quality, formats[f]);
    }
    if (!InsertMenuW(menu, position, MF_BYPOSITION | MF_POPUP, (UINT_PTR)root, L"Convert Image")) {
        DestroyMenu(root); return E_FAIL;
    }
    return MAKE_HRESULT(SEVERITY_SUCCESS, 0, 15);
}

static HRESULT launch(const std::vector<std::wstring>& paths, UINT command) {
    if (paths.empty() || command >= 15) return E_INVALIDARG;
    wchar_t module[MAX_PATH];
    DWORD size = GetModuleFileNameW(moduleHandle, module, MAX_PATH);
    if (!size || size >= MAX_PATH) return E_FAIL;
    std::wstring folder(module, size);
    folder.resize(folder.find_last_of(L"\\/"));
    std::wstring app = folder + L"\\ConvertImage.exe";
    if (GetFileAttributesW(app.c_str()) == INVALID_FILE_ATTRIBUTES) return HRESULT_FROM_WIN32(ERROR_FILE_NOT_FOUND);
    wchar_t temp[MAX_PATH], request[MAX_PATH];
    if (!GetTempPathW(MAX_PATH, temp) || !GetTempFileNameW(temp, L"cim", 0, request)) return E_FAIL;
    std::string payload = "{\"format\":\"" + std::string(formatIds[command / 3]) + "\",\"mode\":\"" + presetIds[command % 3] + "\",\"files\":[";
    for (size_t i = 0; i < paths.size(); ++i) {
        if (i) payload += ',';
        payload += jsonString(paths[i]);
    }
    payload += "]}";
    HANDLE file = CreateFileW(request, GENERIC_WRITE, 0, nullptr, TRUNCATE_EXISTING, FILE_ATTRIBUTE_TEMPORARY, nullptr);
    if (file == INVALID_HANDLE_VALUE) { DeleteFileW(request); return E_FAIL; }
    DWORD written = 0;
    bool saved = WriteFile(file, payload.data(), (DWORD)payload.size(), &written, nullptr) && written == payload.size();
    CloseHandle(file);
    if (!saved) { DeleteFileW(request); return E_FAIL; }
    // Paths travel in UTF-8 JSON, never through cmd.exe or a command line per image.
    std::wstring cmd = L"\"" + app + L"\" --request \"" + request + L"\"";
    STARTUPINFOW startup{sizeof(startup)};
    PROCESS_INFORMATION process{};
    if (!CreateProcessW(app.c_str(), cmd.data(), nullptr, nullptr, FALSE, 0, nullptr, folder.c_str(), &startup, &process)) {
        DWORD error = GetLastError(); DeleteFileW(request); return HRESULT_FROM_WIN32(error);
    }
    CloseHandle(process.hThread);
    CloseHandle(process.hProcess);
    return S_OK;
}

class Menu final : public IShellExtInit, public IContextMenu {
    std::atomic<ULONG> refs{1};
    std::vector<std::wstring> paths;
public:
    Menu() { ++objects; }
    ~Menu() { --objects; }
    HRESULT STDMETHODCALLTYPE QueryInterface(REFIID iid, void** out) override {
        if (!out) return E_POINTER;
        *out = nullptr;
        if (iid == IID_IUnknown || iid == IID_IShellExtInit) *out = static_cast<IShellExtInit*>(this);
        else if (iid == IID_IContextMenu) *out = static_cast<IContextMenu*>(this);
        else return E_NOINTERFACE;
        AddRef(); return S_OK;
    }
    ULONG STDMETHODCALLTYPE AddRef() override { return ++refs; }
    ULONG STDMETHODCALLTYPE Release() override { ULONG n = --refs; if (!n) delete this; return n; }
    HRESULT STDMETHODCALLTYPE Initialize(PCIDLIST_ABSOLUTE, IDataObject* data, HKEY) override {
        paths.clear();
        if (!data) return E_INVALIDARG;
        FORMATETC format{CF_HDROP, nullptr, DVASPECT_CONTENT, -1, TYMED_HGLOBAL};
        STGMEDIUM medium{};
        HRESULT hr = data->GetData(&format, &medium);
        if (FAILED(hr)) return hr;
        paths = readDrop((HDROP)medium.hGlobal);
        ReleaseStgMedium(&medium);
        return paths.empty() ? E_INVALIDARG : S_OK;
    }
    HRESULT STDMETHODCALLTYPE QueryContextMenu(HMENU menu, UINT pos, UINT first, UINT last, UINT flags) override {
        if (paths.empty() || flags & CMF_DEFAULTONLY) return MAKE_HRESULT(SEVERITY_SUCCESS, 0, 0);
        return buildMenu(menu, pos, first, last);
    }
    HRESULT STDMETHODCALLTYPE InvokeCommand(CMINVOKECOMMANDINFO* info) override {
        if (!info || HIWORD(info->lpVerb)) return E_INVALIDARG;
        HRESULT result = launch(paths, LOWORD(info->lpVerb));
        if (FAILED(result) && !(info->fMask & CMIC_MASK_FLAG_NO_UI))
            MessageBoxW(info->hwnd, L"Convert Image gagal dimulai. Jalankan kembali installer untuk memperbaiki pemasangan.", L"Convert Image", MB_OK | MB_ICONERROR);
        return result;
    }
    HRESULT STDMETHODCALLTYPE GetCommandString(UINT_PTR id, UINT flags, UINT*, LPSTR name, UINT count) override {
        if (id >= 15) return E_INVALIDARG;
        if ((flags == GCS_VERBW || flags == GCS_HELPTEXTW) && name && count) {
            std::wstring text = flags == GCS_VERBW ? L"ConvertImage" + std::to_wstring(id) : L"Simpan hasil sebagai file baru";
            wcsncpy_s((wchar_t*)name, count, text.c_str(), _TRUNCATE);
        } else if ((flags == GCS_VERBA || flags == GCS_HELPTEXTA) && name && count) {
            std::string text = "ConvertImage" + std::to_string(id);
            strncpy_s(name, count, text.c_str(), _TRUNCATE);
        }
        return S_OK;
    }
};

class Factory final : public IClassFactory {
    std::atomic<ULONG> refs{1};
public:
    Factory() { ++objects; }
    ~Factory() { --objects; }
    HRESULT STDMETHODCALLTYPE QueryInterface(REFIID iid, void** out) override {
        if (!out) return E_POINTER;
        *out = nullptr;
        if (iid != IID_IUnknown && iid != IID_IClassFactory) return E_NOINTERFACE;
        *out = this; AddRef(); return S_OK;
    }
    ULONG STDMETHODCALLTYPE AddRef() override { return ++refs; }
    ULONG STDMETHODCALLTYPE Release() override { ULONG n = --refs; if (!n) delete this; return n; }
    HRESULT STDMETHODCALLTYPE CreateInstance(IUnknown* outer, REFIID iid, void** out) override {
        if (outer) return CLASS_E_NOAGGREGATION;
        auto menu = new(std::nothrow) Menu();
        if (!menu) return E_OUTOFMEMORY;
        HRESULT hr = menu->QueryInterface(iid, out); menu->Release(); return hr;
    }
    HRESULT STDMETHODCALLTYPE LockServer(BOOL lock) override { if (lock) ++objects; else --objects; return S_OK; }
};

STDAPI DllGetClassObject(REFCLSID clsid, REFIID iid, void** out) {
    if (clsid != CLSID_ConvertImage) return CLASS_E_CLASSNOTAVAILABLE;
    auto factory = new(std::nothrow) Factory();
    if (!factory) return E_OUTOFMEMORY;
    HRESULT hr = factory->QueryInterface(iid, out); factory->Release(); return hr;
}
STDAPI DllCanUnloadNow() { return objects == 0 ? S_OK : S_FALSE; }
BOOL WINAPI DllMain(HINSTANCE instance, DWORD reason, LPVOID) {
    if (reason == DLL_PROCESS_ATTACH) { moduleHandle = instance; DisableThreadLibraryCalls(instance); }
    return TRUE;
}

#ifdef CONVERT_IMAGE_TEST
// Native contract check, compiled only into the CI test executable.
int wmain(int argc, wchar_t** argv) {
    if (argc != 3) return 1;
    std::vector<std::wstring> paths{argv[1], argv[2]};
    for (const auto& p : paths) if (!supported(p)) return 2;
    if (supported(L"C:\\invalid-file.txt")) return 3;
    std::wstring joined = paths[0] + L'\0' + paths[1] + L'\0' + L'\0';
    SIZE_T bytes = sizeof(DROPFILES) + joined.size() * sizeof(wchar_t);
    HGLOBAL drop = GlobalAlloc(GHND, bytes);
    auto content = (DROPFILES*)GlobalLock(drop);
    content->pFiles = sizeof(DROPFILES); content->fWide = TRUE;
    memcpy((BYTE*)content + sizeof(DROPFILES), joined.data(), joined.size() * sizeof(wchar_t));
    GlobalUnlock(drop);
    bool selected = readDrop((HDROP)drop) == paths;
    GlobalFree(drop);
    if (!selected) return 4;
    HMENU menu = CreatePopupMenu();
    if (HRESULT_CODE(buildMenu(menu, 0, 20, 100)) != 15) return 5;
    HMENU root = GetSubMenu(menu, 0);
    if (GetMenuItemCount(root) != 5) return 6;
    for (UINT f = 0; f < 5; ++f) {
        HMENU sub = GetSubMenu(root, f);
        if (GetMenuItemCount(sub) != 3) return 7;
        for (UINT p = 0; p < 3; ++p) if (GetMenuItemID(sub, p) != 20 + f * 3 + p) return 8;
    }
    DestroyMenu(menu);
    if (jsonString(L"foto ü & [1].png").find("ü") == std::string::npos) return 9;
    if (jsonString(L"a\\b\"c") != "\"a\\\\b\\\"c\"") return 10;
    void* factory = nullptr;
    if (FAILED(DllGetClassObject(CLSID_ConvertImage, IID_IClassFactory, &factory))) return 11;
    IContextMenu* instance = nullptr;
    HRESULT hr = ((IClassFactory*)factory)->CreateInstance(nullptr, IID_IContextMenu, (void**)&instance);
    ((IClassFactory*)factory)->Release();
    if (FAILED(hr)) return 12;
    instance->Release();
    return DllCanUnloadNow() == S_OK ? 0 : 13;
}
#endif
