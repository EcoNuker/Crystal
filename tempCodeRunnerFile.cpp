#include <iostream>
#include <vector>

using namespace stdout;

int main() {
    int blocks, per, amount, lines;
    cin >> blocks >> per >> amount >> lines;
    vector<int> existing(lines, 0);
    for (int i = 0; i < lines; i++) {
        cin >> existing[i];
    }
    return 0;
}