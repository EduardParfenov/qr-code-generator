const assert = require('assert');

function formatPhone(value) {
    let rest = value.replace(/^\+7\(?/, '');
    let digits = rest.replace(/\D/g, '');
    if (digits.length === 11 && (digits.charAt(0) === '7' || digits.charAt(0) === '8')) {
        digits = digits.slice(1);
    }
    digits = digits.slice(0, 10);
    const p1 = digits.slice(0, 3);
    const p2 = digits.slice(3, 6);
    const p3 = digits.slice(6, 8);
    const p4 = digits.slice(8, 10);
    let result = '';
    if (p1) result = '+7(' + p1;
    if (p1.length === 3 && p2) result += ')';
    if (p2) result += p2;
    if (p3) result += '-' + p3;
    if (p4) result += '-' + p4;
    return result;
}

function test(description, fn) {
    try {
        fn();
        console.log(`  ✓ ${description}`);
    } catch (e) {
        console.error(`  ✗ ${description}`);
        console.error(`    ${e.message}`);
        process.exitCode = 1;
    }
}

console.log('formatPhone tests:');

test('полный номер с +7', () => {
    assert.strictEqual(formatPhone('+7(900)111-22-33'), '+7(900)111-22-33');
});

test('номер с 8 вместо +7', () => {
    assert.strictEqual(formatPhone('8(900)111-22-33'), '+7(900)111-22-33');
});

test('номер без кода страны', () => {
    assert.strictEqual(formatPhone('9001112233'), '+7(900)111-22-33');
});

test('номер с 800 (не отбрасывает 8)', () => {
    assert.strictEqual(formatPhone('+7(800)000-00-00'), '+7(800)000-00-00');
});

test('обрезка до 10 цифр', () => {
    assert.strictEqual(formatPhone('+7(900)111-22-33-44-55'), '+7(900)111-22-33');
});

test('только 3 цифры', () => {
    assert.strictEqual(formatPhone('900'), '+7(900');
});

test('4 цифры — скобка закрывается', () => {
    assert.strictEqual(formatPhone('9001'), '+7(900)1');
});

test('пустой ввод', () => {
    assert.strictEqual(formatPhone(''), '');
});

test('буквы игнорируются', () => {
    assert.strictEqual(formatPhone('abc900def111ghi22jkl33'), '+7(900)111-22-33');
});

if (process.exitCode) {
    console.error('\nТесты провалены!');
} else {
    console.log('\nВсе тесты пройдены!');
}
